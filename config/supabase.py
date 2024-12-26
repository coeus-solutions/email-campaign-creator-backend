from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SupabaseSettings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

settings = SupabaseSettings()

logger.debug(f"Initializing Supabase client with URL: {settings.supabase_url}")
try:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise 