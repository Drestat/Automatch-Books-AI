import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Easy Bank Transactions"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "qbo_mirror")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

    # QuickBooks Settings (Shared across SaaS)
    QBO_CLIENT_ID: str = os.getenv("QBO_CLIENT_ID", "")
    QBO_CLIENT_SECRET: str = os.getenv("QBO_CLIENT_SECRET", "")
    QBO_REDIRECT_URI: str = os.getenv("QBO_REDIRECT_URI", "http://localhost:3000/callback")
    QBO_ENVIRONMENT: str = os.getenv("QBO_ENVIRONMENT", "sandbox")

    # AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        case_sensitive = True

settings = Settings()
