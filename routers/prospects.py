from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import csv
import io
from datetime import datetime
from config.supabase import supabase

router = APIRouter()

class ProspectCreate(BaseModel):
    email: EmailStr
    full_name: str
    company: Optional[str] = None
    custom_fields: Optional[dict] = None

class ProspectResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    custom_fields: Optional[dict]
    created_at: datetime
    updated_at: datetime

@router.post("/upload", response_model=dict)
async def upload_prospects(file: UploadFile = File(...)):
    try:
        # Read the CSV file
        contents = await file.read()
        csv_data = contents.decode('utf-8-sig')  # Use utf-8-sig to handle BOM
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        prospects_count = 0
        errors = []
        
        for row in csv_reader:
            try:
                # Map CSV columns to prospect fields, handling different possible column names
                email = row.get('email') or row.get('Email') or row.get('EMAIL')
                full_name = row.get('full_name') or row.get('Full Name') or row.get('Name') or row.get('FULL_NAME')
                company = row.get('company') or row.get('Company') or row.get('COMPANY')
                
                if not email or not full_name:
                    raise ValueError("Email and Full Name are required fields")
                
                # Create prospect from CSV row
                prospect = {
                    "email": email,
                    "full_name": full_name,
                    "company": company,
                    "custom_fields": {}
                }
                
                # Add any additional columns as custom fields
                for key, value in row.items():
                    normalized_key = key.lower()
                    if normalized_key not in ['email', 'full_name', 'name', 'company', 'full name']:
                        prospect['custom_fields'][key] = value
                
                # Insert into database
                result = supabase.table('prospects').insert(prospect).execute()
                prospects_count += 1
            except Exception as e:
                errors.append(f"Error on row {prospects_count + 1}: {str(e)}")
        
        return {
            "prospects_count": prospects_count,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=ProspectResponse)
async def create_prospect(prospect: ProspectCreate):
    try:
        result = supabase.table('prospects').insert({
            "email": prospect.email,
            "full_name": prospect.full_name,
            "company": prospect.company,
            "custom_fields": prospect.custom_fields
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(prospect_id: str, prospect: ProspectCreate):
    try:
        # Check if prospect exists
        existing = supabase.table('prospects').select("*").eq('id', prospect_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        # Update prospect
        result = supabase.table('prospects').update({
            "email": prospect.email,
            "full_name": prospect.full_name,
            "company": prospect.company,
            "custom_fields": prospect.custom_fields,
            "updated_at": datetime.utcnow().isoformat()
        }).eq('id', prospect_id).execute()
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{prospect_id}")
async def delete_prospect(prospect_id: str):
    try:
        # Check if prospect exists
        existing = supabase.table('prospects').select("*").eq('id', prospect_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        # Delete prospect
        supabase.table('prospects').delete().eq('id', prospect_id).execute()
        return {"message": "Prospect deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(prospect_id: str):
    try:
        result = supabase.table('prospects').select("*").eq('id', prospect_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Prospect not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ProspectResponse])
async def list_prospects():
    try:
        result = supabase.table('prospects').select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 