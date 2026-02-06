
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def check_tx():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Search for A1 Rental or recently created
    query = """
    SELECT id, description, amount, status, transaction_type, tags, note, sync_token, realm_id
    FROM transactions 
    WHERE description ILIKE '%A1 Rental%' 
       OR created_at > NOW() - INTERVAL '1 day'
    ORDER BY created_at DESC
    LIMIT 10;
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} matching transactions:")
    for row in rows:
        print(row)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_tx()
