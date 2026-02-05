import modal
from dotenv import dotenv_values
import os

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
)

app = modal.App("check-tx-count")

@app.local_entrypoint()
def main():
    count_txs.remote()

@app.function(image=image)
def count_txs():
    import sys
    sys.path.append("/root")
    from app.db.session import SessionLocal
    from app.models.qbo import Transaction, QBOConnection

    db = SessionLocal()
    try:
        count = db.query(Transaction).count()
        print(f"📊 Total Transactions in DB: {count}")
        
        connections = db.query(QBOConnection).all()
        print(f"🔗 Total Connections: {len(connections)}")
        for conn in connections:
            tx_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
            print(f"   Realm {conn.realm_id}: {tx_count} txs")
            
    finally:
        db.close()
