
import asyncio
import os
import psycopg2
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient
from dotenv import load_dotenv
import json

load_dotenv()

async def compare_dates(realm_id, tx_ids):
    db = SessionLocal()
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        qbo_conn = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, qbo_conn)
        
        print(f"{'ID':<10} | {'Description':<30} | {'DB Date':<12} | {'QBO Date':<12} | {'Match?'}")
        print("-" * 80)
        
        for tx_id in tx_ids:
            # Get DB Date
            cur.execute("SELECT description, date FROM transactions WHERE id = %s AND realm_id = %s", (tx_id, realm_id))
            db_row = cur.fetchone()
            db_desc = db_row[0] if db_row else "NOT FOUND"
            db_date = str(db_row[1]) if db_row else "N/A"
            
            # Get QBO Date
            qbo_date = "N/A"
            try:
                # We need to know the type to use the right getter, but most are purchases
                # Try get_purchase first
                try:
                    res = await client.get_purchase(tx_id)
                    qbo_date = res.get("Purchase", {}).get("TxnDate") or res.get("TxnDate", "N/A")
                except:
                    # Fallback to generic query if type is different
                    res = await client.request("GET", f"purchase/{tx_id}")
                    qbo_date = res.get("Purchase", {}).get("TxnDate", "N/A")
            except Exception as e:
                qbo_date = f"ERR: {str(e)[:10]}"

            match = "✅" if db_date == qbo_date else "❌"
            print(f"{tx_id:<10} | {db_desc[:30]:<30} | {db_date:<12} | {qbo_date:<12} | {match}")
            
    finally:
        cur.close()
        conn.close()
        db.close()

if __name__ == "__main__":
    # Recently discussed IDs
    ids = ['84', '151', '77', '138', '115']
    asyncio.run(compare_dates('9341456245321396', ids))
