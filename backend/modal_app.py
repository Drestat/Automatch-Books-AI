import modal
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.transaction_service import TransactionService
from app.services.analysis_service import AnalysisService

# Define the image with necessary dependencies
# Note: modal.Image.debian_slim() is a good default
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "sqlalchemy",
    "psycopg2-binary",
    "intuit-oauth",
    "requests",
    "google-generativeai",
    "pydantic-settings"
)

app = modal.App("qbo-sync-engine", image=image)

# Define secrets for environment variables
secrets = modal.Secret.from_dict({
    "POSTGRES_USER": settings.POSTGRES_USER,
    "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
    "POSTGRES_DB": settings.POSTGRES_DB,
    "POSTGRES_HOST": settings.POSTGRES_HOST,
    "QBO_CLIENT_ID": settings.QBO_CLIENT_ID,
    "QBO_CLIENT_SECRET": settings.QBO_CLIENT_SECRET,
    "QBO_REDIRECT_URI": settings.QBO_REDIRECT_URI,
    "QBO_ENVIRONMENT": settings.QBO_ENVIRONMENT,
    "GEMINI_API_KEY": settings.GEMINI_API_KEY,
})

@app.function(secrets=[secrets])
def sync_user_data(realm_id: str):
    """Triggers a full sync for a specific QBO realm"""
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print(f"❌ No connection found for realm {realm_id}")
            return
        
        sync_service = TransactionService(db, connection)
        print(f"🔄 Starting background sync for {realm_id}...")
        sync_service.sync_all()
        print(f"✅ Sync complete for {realm_id}")
    finally:
        db.close()

@app.function(secrets=[secrets])
def process_ai_categorization(realm_id: str, limit: int = 20, tx_id: str = None):
    """Triggers AI categorization for unmatched transactions"""
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print(f"❌ No connection found for realm {realm_id}")
            return
        
        analysis_service = AnalysisService(db, connection.realm_id) # AnalysisService takes realm_id string, not connection obj
        print(f"🧠 Starting AI categorization for {realm_id} {'(specific ID: ' + tx_id + ')' if tx_id else ''}...")
        results = analysis_service.analyze_transactions(limit=limit, tx_id=tx_id)
        print(f"✅ AI categorization complete for {realm_id}. Processed {len(results) if isinstance(results, list) else 0} TXs.")
    finally:
        db.close()

@app.function(secrets=[secrets], schedule=modal.Period(days=1))
def daily_maintenance():
    """Daily CRON job to sync and process all active connections"""
    db = SessionLocal()
    try:
        connections = db.query(QBOConnection).all()
        for conn in connections:
            print(f"🚀 Triggering daily tasks for {conn.realm_id}")
            sync_user_data.remote(conn.realm_id)
            process_ai_categorization.remote(conn.realm_id)
    finally:
        db.close()
