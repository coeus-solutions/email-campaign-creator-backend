from pydantic_settings import BaseSettings

class OpenAISettings(BaseSettings):
    api_key: str

    model_config = {
        'env_file': '.env',
        'env_prefix': 'OPENAI_'
    }

openai_settings = OpenAISettings() 