import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Automatch Books AI"
    API_V1_STR: str = "/api/v1"
    NEXT_PUBLIC_APP_URL: str = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "qbo_mirror")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    
    # Priority: Env variable > Calculated slug
    # Using a field that will be overridden by env if present
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            # Default for local dev (no SSL by default unless specified)
            ssl_mode = "require" if self.POSTGRES_HOST != "localhost" else "prefer"
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}?sslmode={ssl_mode}"

    # Security
    BACKEND_CORS_ORIGINS: list[str] = [
        "https://automatchbooksai.com",
        "https://www.automatchbooksai.com",
        "http://localhost:3000",  # Local dev only
    ]
    FERNET_KEY: str = os.getenv("FERNET_KEY", "")

    # QuickBooks Settings (Shared across SaaS)
    QBO_CLIENT_ID: str = os.getenv("QBO_CLIENT_ID", "")
    QBO_CLIENT_SECRET: str = os.getenv("QBO_CLIENT_SECRET", "")
    QBO_REDIRECT_URI: str = os.getenv("QBO_REDIRECT_URI", "https://automatchbooksai.com/callback")
    QBO_ENVIRONMENT: str = os.getenv("QBO_ENVIRONMENT", "sandbox")
    QBO_WEBHOOK_VERIFIER: str = os.getenv("QBO_WEBHOOK_VERIFIER", "")

    # AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_MONTHLY_PRICE_ID: str = os.getenv("STRIPE_MONTHLY_PRICE_ID", "") # Legacy/Default
    
    # Tiered Pricing
    STRIPE_PRICE_ID_TIER_1: str = os.getenv("STRIPE_PRICE_ID_TIER_1", "") # 1 Account
    STRIPE_PRICE_ID_TIER_2: str = os.getenv("STRIPE_PRICE_ID_TIER_2", "") # 4 Accounts
    STRIPE_PRICE_ID_TIER_3: str = os.getenv("STRIPE_PRICE_ID_TIER_3", "") # 10 Accounts
    
    # Clerk Settings
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")

    # Admin God Mode Whitelist (Clerk User IDs)
    ADMIN_USERS: list[str] = [
        "user_38gfoio189CGrr2AO1a9ssier7w", # User 1
        "user_395GWw3SraKqcc7qjFToVMxH5v1", # User 2 (Likely Developer)
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Allow extra fields (like frontend keys) in the .env file

settings = Settings()
