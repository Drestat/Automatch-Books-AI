from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router

# v4.3.2 - GLOBAL SUGGESTION PURGE + FRONTEND STRICTNESS

def initialize_app_logic():
    """Compatibility wrapper for Modal cloud deployment.
    Signal that the app module has loaded correctly.
    Startup logic is now handled in the lifespan context manager.
    """
    print("🚀 [main.py] initialize_app_logic called (Compatibility Mode)")
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(">>> [main.py] Initializing and Repairing Models...")
    try:
        from app.db.session import engine, Base
        from sqlalchemy import text
        from app.models.gamification import UserGamificationStats, GamificationEvent
        
        # Ensure tables exist (for new tables)
        Base.metadata.create_all(bind=engine)
        
        
        # Schema repair handled by Alembic/Migration scripts now.
        # Manual patches removed.
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
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "4.5.0"}

@app.get("/")
def read_root():
    return {
        "message": "Automatch Books AI API is ONLINE",
        "version": "4.5.0",
        "status": "ready"
    }

from fastapi.staticfiles import StaticFiles
import os

# Mount uploads for receipt preview
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)
