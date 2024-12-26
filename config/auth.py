from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

auth_settings = AuthSettings() 