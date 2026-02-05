import modal
from dotenv import dotenv_values

app = modal.App("integrity-check")
env_vars = dotenv_values(".env")

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
        "httpx",
        "google-generativeai",
        "stripe",
        "rapidfuzz",
        "python-multipart",
        "pytz",
        "alembic"
    )
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
    .add_local_dir("alembic", remote_path="/root/alembic")
    .add_local_file("alembic.ini", remote_path="/root/alembic.ini")
)

@app.local_entrypoint()
def main():
    check_imports.remote()

@app.function(image=image)
def check_imports():
    import sys
    sys.path.append("/root")
    
    print("Checking imports...")
    try:
        print("Importing app.api.deps...")
        import app.api.deps
        print("app.api.deps imported.")
        
        print("Importing get_current_user...")
        from app.api.deps import get_current_user
        print(f"get_current_user: {get_current_user}")
        
        print("Importing app.main...")
        import app.main
        print("app.main imported.")
        
    except Exception as e:
        print(f"❌ Import Error: {e}")
        import traceback
        traceback.print_exc()
