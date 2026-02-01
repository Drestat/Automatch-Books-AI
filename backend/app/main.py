from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router

# v3.9.6 - ACCOUNT SYNC DEBUGGING + DB CLEANUP

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(">>> [main.py] Initializing Models...")
    try:
        from app.db.session import engine, Base
        # Ensure tables exist (including new columns)
        Base.metadata.create_all(bind=engine)
        print("✅ [main.py] Database initialized.")
    except Exception as e:
        print(f"❌ [main.py] Database error during startup: {e}")
    
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
    return {"status": "ok", "version": "3.9.5-prod"}

@app.get("/")
def read_root():
    return {
        "message": "Automatch Books AI API is ONLINE",
        "version": "3.9.5",
        "status": "ready"
    }

def initialize_app_logic():
    return True



