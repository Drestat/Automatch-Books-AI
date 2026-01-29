import modal
from sqlalchemy import create_engine, text
import os

app = modal.App("db-maintenance")

image = modal.Image.debian_slim().pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv")

from dotenv import dotenv_values
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = dotenv_values(env_path)
secrets = modal.Secret.from_dict(env_vars)

@app.function(image=image, secrets=[secrets])
def drop_transactions_table_remote():
    db_url = os.environ["POSTGRES_DB"].replace("postgres://", "postgresql://") # Ensure sqlalchemy format
    if "sslmode" not in db_url:
        db_url += "?sslmode=require"
    
    # Construct full URL if separated (modal secrets usually separate them)
    # Check if we have individual vars or a full URL
    if not db_url.startswith("postgresql"):
        # Reconstruct from parts
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        host = os.environ.get("POSTGRES_HOST")
        dbname = os.environ.get("POSTGRES_DB")
        db_url = f"postgresql://{user}:{password}@{host}/{dbname}?sslmode=require"

    print(f"Connecting to DB...")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Dropping transactions table...")
        conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        conn.commit()
        print("Dropped.")

if __name__ == "__main__":
    with app.run():
        drop_transactions_table_remote.remote()
