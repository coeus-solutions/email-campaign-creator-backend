from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
from config.openai import openai_settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

openai.api_key = openai_settings.api_key

class EmailGenerationRequest(BaseModel):
    productDescription: str
    prompt: str

class EmailContent(BaseModel):
    subject: str
    content: str

@router.post("/generate-email", response_model=EmailContent)
async def generate_email(request: EmailGenerationRequest):
    try:
        # Create a system message that sets up the context
        system_message = """You are an expert email copywriter specializing in creating beautiful, personalized HTML emails. 
        Your task is to create compelling email content that effectively promotes products while maintaining a professional 
        and engaging tone. Generate both a subject line and HTML email body that are persuasive but not overly salesy.
        
        Important guidelines:
        1. Use proper HTML formatting for structure and style
        2. Include appropriate spacing and line breaks
        3. Use personalization placeholders correctly
        4. Create visually appealing sections
        5. Include subtle emojis where appropriate
        6. Ensure the email looks good on all devices"""

        # Create the user message combining product description and specific instructions
        user_message = f"""Product Description: {request.productDescription}

Additional Instructions: {request.prompt}

Please generate an email that:
1. Uses proper HTML formatting
2. Includes personalization placeholders
3. Has a clear visual hierarchy
4. Is mobile-responsive
5. Has an engaging call-to-action

Format the response exactly as:
SUBJECT: [subject line]
CONTENT: [HTML email content]"""

        # Call OpenAI API
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000  # Increased for HTML content
        )

        # Extract subject and content from the response
        generated_text = response['choices'][0]['message']['content']
        subject_line = ""
        content = ""

        # Parse the response
        parts = generated_text.split("CONTENT:")
        if len(parts) == 2:
            subject_part = parts[0].split("SUBJECT:")[1].strip()
            content_part = parts[1].strip()
            subject_line = subject_part
            content = content_part

        return EmailContent(subject=subject_line, content=content)

    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 