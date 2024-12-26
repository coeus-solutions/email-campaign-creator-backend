from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from config.supabase import supabase
from config.auth import auth_settings
from typing import Optional
import logging
import uuid
from datetime import datetime
import re
import json
import traceback

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configure logging format
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Email validation regex
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        # Verify the JWT token using Supabase
        user = supabase.auth.get_user(credentials.credentials)
        return user.user.id
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

    @validator('email')
    def validate_email(cls, v):
        if not EMAIL_REGEX.match(v):
            raise ValueError('Invalid email format')
        return v.lower()  # Normalize email to lowercase

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123",
                "full_name": "John Doe"
            }
        }

class UserLogin(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        if not EMAIL_REGEX.match(v):
            raise ValueError('Invalid email format')
        return v.lower()  # Normalize email to lowercase

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str

@router.get("/test-connection")
async def test_connection():
    try:
        # Test the connection by fetching the user count
        result = supabase.table('users').select("*", count='exact').execute()
        return {"status": "success", "user_count": len(result.data)}
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.post("/test-create-user")
async def test_create_user():
    try:
        # Try to create a user directly in the users table
        user_data = supabase.table('users').insert({
            "id": str(uuid.uuid4()),
            "email": "test.direct@example.com",
            "full_name": "Test Direct User"
        }).execute()
        
        return {"status": "success", "user": user_data.data[0]}
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    try:
        logger.info(f"Starting signup process for email: {user.email}")
        logger.debug(f"Full signup request data: {user.dict()}")
        
        # Try to create the auth user
        try:
            logger.debug("Attempting to create auth user with Supabase")
            
            # Create user in auth.users
            auth_response = supabase.auth.admin.create_user({
                "email": user.email,
                "password": user.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": user.full_name
                }
            })
            logger.debug(f"Raw Supabase response: {auth_response}")
            
            if not auth_response.user:
                logger.error("Auth response did not contain user data")
                raise HTTPException(status_code=400, detail="Failed to create user account")
            
            logger.info(f"Successfully created auth user with ID: {auth_response.user.id}")
            
            try:
                # Create user profile in users table
                user_data = supabase.table('users').insert({
                    "id": auth_response.user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "password_hash": "MANAGED_BY_SUPABASE_AUTH"  # Placeholder value
                }).execute()
                
                logger.debug(f"User profile created: {user_data}")
            except Exception as profile_error:
                logger.error(f"Failed to create user profile: {str(profile_error)}")
                # If profile creation fails, we should delete the auth user
                try:
                    supabase.auth.admin.delete_user(auth_response.user.id)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup auth user: {str(cleanup_error)}")
                raise profile_error
            
            # Return user data
            return {
                "id": auth_response.user.id,
                "email": user.email,
                "full_name": user.full_name
            }
            
        except Exception as auth_error:
            logger.error(f"Supabase auth error: {str(auth_error)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            if hasattr(auth_error, 'message'):
                raise HTTPException(status_code=400, detail=auth_error.message)
            raise HTTPException(status_code=400, detail=str(auth_error))
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/login")
async def login(user: UserLogin):
    try:
        logger.info(f"Attempting login for email: {user.email}")
        auth_response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        logger.info("Login successful")
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Invalid credentials") 

@router.get("/test-supabase")
async def test_supabase():
    try:
        logger.info("Testing Supabase client functionality")
        
        # Test database connection
        db_result = supabase.table('users').select("*", count='exact').execute()
        logger.debug(f"Database test result: {db_result}")
        
        # Test auth functionality
        auth_result = supabase.auth.get_session()
        logger.debug(f"Auth test result: {auth_result}")
        
        return {
            "status": "success",
            "db_test": "passed" if db_result else "failed",
            "auth_test": "passed" if auth_result else "failed"
        }
    except Exception as e:
        logger.error(f"Supabase test error: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)) 