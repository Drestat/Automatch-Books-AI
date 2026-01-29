
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("backend/.env")

# Database Connection (Hardcoded from previous successful step if env fails, but let's try env first or fallback)
user = os.getenv("POSTGRES_USER", "neondb_owner")
password = os.getenv("POSTGRES_PASSWORD", "npg_kETgK4j8fUNM")
host = os.getenv("POSTGRES_HOST", "ep-broad-wildflower-ahi897rz-pooler.c-3.us-east-1.aws.neon.tech")
db_name = os.getenv("POSTGRES_DB", "neondb")
db_url = f"postgresql://{user}:{password}@{host}/{db_name}?sslmode=require"

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Connecting to database...")
    try:
        # Check if column exists
        check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='transactions' AND column_name='suggested_tags';")
        result = conn.execute(check_query).fetchone()
        
        if result:
            print("Column 'suggested_tags' already exists.")
        else:
            print("Adding column 'suggested_tags' to 'transactions' table...")
            conn.execute(text("ALTER TABLE transactions ADD COLUMN suggested_tags JSONB DEFAULT '[]'::jsonb;"))
            conn.commit()
            print("Column added successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
