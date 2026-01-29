import modal
from dotenv import dotenv_values
import os
import sys

# Ensure we can import app models
sys.path.append("/root")

app = modal.App("db-maintenance")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv")
    .add_local_dir("app", remote_path="/root/app")
)

env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = dotenv_values(env_path)
secrets = modal.Secret.from_dict(env_vars)

@app.function(image=image, secrets=[secrets])
def create_missing_tables():
    from sqlalchemy import create_engine
    from app.db.session import Base
    from app.models.qbo import BankAccount, Tag # Import to register with Base
    
    db_url = os.environ["POSTGRES_DB"].replace("postgres://", "postgresql://")
    if "sslmode" not in db_url:
        db_url += "?sslmode=require"
    
     # Handle separated vars if needed
    if not db_url.startswith("postgresql"):
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        host = os.environ.get("POSTGRES_HOST")
        dbname = os.environ.get("POSTGRES_DB")
        db_url = f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

    print(f"Connecting to DB...")
    engine = create_engine(db_url)
    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables verified/created.")

if __name__ == "__main__":
    with app.run():
        create_missing_tables.remote()
