import modal
import os
from dotenv import dotenv_values

# 1. PRE-DEPLOY: Capture production keys from disk
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = dotenv_values(env_path)

# 2. IMAGE DEFINITION
image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi", 
        "uvicorn", 
        "psycopg2-binary", 
        "pydantic-settings", 
        "python-dotenv",
        "sqlalchemy",
        "intuit-oauth",
        "requests",
        "google-generativeai",
        "stripe",
        "rapidfuzz",
        "python-multipart"
    )
    .add_local_dir("./app", remote_path="/root/app")
)

app = modal.App("qbo-sync-engine")

# 3. SECRETS
secrets = modal.Secret.from_dict({
    "POSTGRES_USER": env_vars.get("POSTGRES_USER", ""),
    "POSTGRES_PASSWORD": env_vars.get("POSTGRES_PASSWORD", ""),
    "POSTGRES_HOST": env_vars.get("POSTGRES_HOST", ""),
    "POSTGRES_DB": env_vars.get("POSTGRES_DB", ""),
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
    "GEMINI_API_KEY": env_vars.get("GEMINI_API_KEY", ""),
})

@app.function(image=image, secrets=[secrets], min_containers=1)
@modal.asgi_app()
def fastapi_app():
    print("🚀 [Modal] ASGI Entrypoint waking up...")
    
    # Imports happen ONLY inside the cloud container
    import sys
    # Add /root to path so 'import app' works (app is at /root/app)
    if "/root" not in sys.path:
        sys.path.append("/root")
    
    try:
        from app.main import app as main_app
        from app.main import initialize_app_logic
        
        # Load the routers and models
        success = initialize_app_logic()
        
        if not success:
            print("⚠️ [Modal] Warning: App initialized with errors.")
            
        print("✅ [Modal] Ready to serve production traffic.")
        return main_app
    except Exception as e:
        print(f"❌ [Modal] CRITICAL STARTUP ERROR: {e}")
        # Return a fallback app so the container stays healthy but reports the error
        from fastapi import FastAPI
        err_app = FastAPI()
        @err_app.get("/{path:path}")
        def err(path: str):
            return {"error": "Startup Failed", "detail": str(e)}
        return err_app

@app.function(image=image, secrets=[secrets])
def daily_maintenance():
    print("Running daily maintenance tasks...")
