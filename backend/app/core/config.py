import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Automatch Books AI"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "qbo_mirror")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

    # Security
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # QuickBooks Settings (Shared across SaaS)
    QBO_CLIENT_ID: str = os.getenv("QBO_CLIENT_ID", "")
    QBO_CLIENT_SECRET: str = os.getenv("QBO_CLIENT_SECRET", "")
    QBO_REDIRECT_URI: str = os.getenv("QBO_REDIRECT_URI", "http://localhost:3000/callback")
    QBO_ENVIRONMENT: str = os.getenv("QBO_ENVIRONMENT", "sandbox")
    QBO_WEBHOOK_VERIFIER: str = os.getenv("QBO_WEBHOOK_VERIFIER", "")

    # AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_MONTHLY_PRICE_ID: str = os.getenv("STRIPE_MONTHLY_PRICE_ID", "")
    
    # Clerk Settings
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
