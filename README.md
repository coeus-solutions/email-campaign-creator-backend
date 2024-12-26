# Email Campaign Backend

FastAPI backend for the Email Campaign application integrated with Supabase.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your Supabase credentials and other configuration

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
Backend/
├── config/
│   └── supabase.py     # Supabase client configuration
├── routers/
│   ├── auth.py         # Authentication endpoints
│   ├── campaigns.py    # Campaign management
│   ├── prospects.py    # Prospect management
│   ├── products.py     # Product management
│   └── gmail.py        # Gmail integration
├── main.py             # FastAPI application
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## API Endpoints

- `/api/auth/*` - Authentication endpoints
- `/api/campaigns/*` - Campaign management
- `/api/prospects/*` - Prospect management
- `/api/products/*` - Product management
- `/api/gmail/*` - Gmail integration

## Development

- The application uses FastAPI for the REST API
- Supabase is used as the database
- Authentication is handled through Supabase 