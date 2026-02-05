import sys
import os
import modal

# Define the Modal app
app = modal.App("inspect-pam-seitz")

# Read env vars
from dotenv import dotenv_values
env_vars = dotenv_values(".env")

# Define the image
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv")
    .env(env_vars)
)

@app.local_entrypoint()
def main():
    print("Starting inspection task...")
    inspect_pam.remote()

@app.function(image=image)
def inspect_pam():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import os

    # Get DB URL from env (injected by Secret)
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment.")
        return

    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        print("Searching for transactions with 'Pam' or 'Seitz'...")
        
        # Search in description
        sql = text("""
            SELECT id, date, description, amount, status, raw_json 
            FROM transactions 
            WHERE description ILIKE '%Pam%' OR description ILIKE '%Seitz%'
        """)
        
        results = session.execute(sql).fetchall()
        
        if not results:
            print("No transactions found matching 'Pam' or 'Seitz' in description.")
            # Try searching in raw_json just in case (slower)
            sql_raw = text("""
                SELECT id, date, description, amount, status, raw_json
                FROM transactions 
                WHERE raw_json::text ILIKE '%Pam%' OR raw_json::text ILIKE '%Seitz%'
            """)
            results = session.execute(sql_raw).fetchall()
            
        if not results:
            print("No transactions found in raw_json either.")
            return

        print(f"Found {len(results)} transactions:")
        for row in results:
            print(f"ID: {row.id}")
            print(f"Date: {row.date}")
            print(f"Description: {row.description}")
            print(f"Amount: {row.amount}")
            print(f"Status: {row.status}")
            print(f"Full Raw Data: {row.raw_json}") 
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()

