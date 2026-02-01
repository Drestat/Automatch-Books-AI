from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

# v3.9.2 - PRODUCTION DEPLOYMENT
app = FastAPI(title="Automatch Books AI")

# CORS - Allow All for Production Resilience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "3.9.2-prod"}

@app.get("/")
def read_root():
    return {
        "message": "Automatch Books AI API is ONLINE",
        "version": "3.9.2",
        "status": "ready"
    }

# Heavy lifting moves into a helper called by the entrypoint
def initialize_app_logic():
    print(">>> [main.py] Initializing API Routes and Models...")
    start_time = time.time()
    try:
        from app.core.config import settings
        from app.api.v1.api import api_router
        from app.db.session import engine, Base
        
        # Ensure tables exist (including new columns)
        Base.metadata.create_all(bind=engine)
        
        # Include the main API router
        app.include_router(api_router, prefix=settings.API_V1_STR)
        
        duration = time.time() - start_time
        print(f"✅ [main.py] App logic initialized in {duration:.2f}s")
        return True
    except Exception as e:
        print(f"❌ [main.py] FAILED to initialize logic: {e}")
        return False
