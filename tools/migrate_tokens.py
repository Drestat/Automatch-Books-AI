from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print("Running Token System Migration...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add token_balance
            conn.execute(text("ALTER TABLE users ADD COLUMN token_balance INTEGER DEFAULT 50"))
            print("✅ Added token_balance")
        except Exception as e:
            print(f"⚠️ token_balance might already exist: {e}")

        try:
            # Add monthly_token_allowance
            conn.execute(text("ALTER TABLE users ADD COLUMN monthly_token_allowance INTEGER DEFAULT 50"))
            print("✅ Added monthly_token_allowance")
        except Exception as e:
            print(f"⚠️ monthly_token_allowance might already exist: {e}")

        try:
            # Add last_refill_date
            # Note: For SQLite/Postgres compatibility we use generic syntax or try/catch specific
            # For Postgres: 
            conn.execute(text("ALTER TABLE users ADD COLUMN last_refill_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
            print("✅ Added last_refill_date")
        except Exception as e:
             print(f"⚠️ last_refill_date might already exist: {e}")
             
    print("Migration Complete.")

if __name__ == "__main__":
    migrate()
