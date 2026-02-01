from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router

# v3.10.1 - TOKEN REFILL + MANUAL AI TRIGGER + BATCH FIX

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(">>> [main.py] Initializing and Repairing Models...")
    try:
        from app.db.session import engine, Base
        from sqlalchemy import text
        
        # Ensure tables exist (for new tables)
        Base.metadata.create_all(bind=engine)
        
        # Repair Schema (Alembic might have missed these if create_all was used first)
        with engine.begin() as conn:
            print("🏗️ [main.py] Running manual schema patches...")
            # BankAccount additions
            conn.execute(text("ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS nickname VARCHAR;"))
            
            # Transactions reasoning (added in previous migration attempts)
            conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS vendor_reasoning VARCHAR;"))
            conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS category_reasoning VARCHAR;"))
            conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS note_reasoning VARCHAR;"))
            conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tax_deduction_note VARCHAR;"))
            
            # QBO Connection updates
            conn.execute(text("ALTER TABLE qbo_connections ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();"))
            
            print("✅ [main.py] Schema repair complete.")
            
        print("✅ [main.py] Database initialized.")
    except Exception as e:
        print(f"❌ [main.py] Database error during startup: {e}")
        import traceback
        print(traceback.format_exc())
    
    yield

app = FastAPI(
    title="Automatch Books AI",
    lifespan=lifespan
)

# CORS - Allow All for Production Resilience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router IMMEDIATELY
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "3.10.1"}

@app.get("/")
def read_root():
    return {
        "message": "Automatch Books AI API is ONLINE",
        "version": "3.10.1",
        "status": "ready"
    }
