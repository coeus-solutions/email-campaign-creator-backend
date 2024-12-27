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
        system_message = """You are an expert B2B email copywriter specializing in creating professional, high-converting outreach emails.

IMPORTANT - Use these exact placeholder formats (do not modify them):
1. {{prospect_name}} - for the recipient's name
2. {{company_name}} - for the recipient's company
3. {{prospect_email}} - for the recipient's email

Guidelines for email creation:
1. Structure:
   - Personal greeting using {{prospect_name}}
   - Strong value proposition
   - Company-specific observation using {{company_name}}
   - Clear call to action
   - Professional signature
2. Styling:
   - Use basic responsive HTML/CSS
   - Use Arial or sans-serif fonts
   - No images, logos, or social links
   - Clean, minimalist design
3. Content:
   - Attention-grabbing subject line
   - Professional tone throughout
   - Concise paragraphs (2-3 lines max)
   - Natural personalization
4. Technical:
   - Ensure high deliverability
   - Mobile-friendly display
   - Clean HTML code
   - Proper spacing and formatting"""

        # Create the user message combining product description and specific instructions
        user_message = f"""Product Description: {request.productDescription}

Additional Instructions: {request.prompt}

Create a professional B2B outreach email that:
1. Uses the exact placeholders: {{prospect_name}}, {{company_name}}, {{prospect_email}}
2. Has an attention-grabbing subject line
3. Follows the structure:
   - Personal greeting
   - Value proposition
   - Company-specific observation
   - Clear call to action
   - Professional signature
4. Includes responsive HTML with clean styling
5. Maintains a professional tone
6. Keeps paragraphs concise

Format the response exactly as:
SUBJECT: [subject line with proper placeholders]
CONTENT: [HTML email content with proper placeholders]"""

        # Call OpenAI API
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000
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

        # Verify and fix any malformed placeholders
        placeholders = [
            ("{{prospect_name}}", ["{full_name}", "{name}"]),
            ("{{prospect_email}}", ["{email}"]),
            ("{{company_name}}", ["{company}", "{prospect_company}"])
        ]
        
        for correct, incorrect_list in placeholders:
            for incorrect in incorrect_list:
                content = content.replace(incorrect, correct)
                subject_line = subject_line.replace(incorrect, correct)

        return EmailContent(subject=subject_line, content=content)

    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 