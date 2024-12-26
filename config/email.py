from pydantic_settings import BaseSettings, SettingsConfigDict

class EmailSettings(BaseSettings):
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

email_settings = EmailSettings() 