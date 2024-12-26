from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, campaigns, prospects, products, openai
from services.email_service import email_service

app = FastAPI(title="Email Campaign API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(prospects.router, prefix="/api/prospects", tags=["Prospects"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(openai.router, prefix="/api/openai", tags=["OpenAI"])

@app.get("/")
async def root():
    return {"message": "Welcome to Email Campaign API"}

@app.get("/test-email")
async def test_email():
    """Test the email configuration."""
    success = email_service.test_connection()
    if success:
        return {"status": "success", "message": "Email configuration is working correctly"}
    else:
        return {"status": "error", "message": "Failed to connect to email server"}

@app.get("/send-test-email/{to_email}")
async def send_test_email(to_email: str):
    """Send a test email to verify the email sending functionality."""
    try:
        success = email_service.send_email(
            to_email=to_email,
            subject="Test Email from Campaign System",
            content="""
            <h1>Test Email</h1>
            <p>This is a test email from your campaign system.</p>
            <p>If you received this email, your email configuration is working correctly!</p>
            """
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Test email sent successfully to {to_email}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 