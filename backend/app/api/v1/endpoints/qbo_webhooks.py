from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
import hashlib
import hmac
import base64
from app.core.config import settings

router = APIRouter()

from app.services.sync_service import SyncService
from app.models.qbo import QBOConnection

@router.post("/webhook")
async def qbo_webhook(
    request: Request,
    intuit_signature: str = Header(None, alias="intuit-signature"),
    db: Session = Depends(get_db)
):
    """
    Verifies signature and triggers background sync for relevant realm_ids.
    """
    payload = await request.body()
    data = await request.json()
    
    # Foundation: Signature verification (Production Ready)
    # Foundation: Signature verification (Production Ready)
    if not intuit_signature:
        raise HTTPException(status_code=401, detail="Missing encoded signature")
        
    verifier = hmac.new(settings.QBO_WEBHOOK_VERIFIER.encode(), payload, hashlib.sha256)
    digest = base64.b64encode(verifier.digest()).decode()
    if digest != intuit_signature:
        raise HTTPException(status_code=401, detail="Invalid signature")

    for notification in data.get("eventNotifications", []):
        realm_id = notification.get("realmId")
        # Find connection for this realm_id
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if connection:
            # Trigger sync
            # In production, this should be a background task (Modal/Celery)
            try:
                service = SyncService(db, connection)
                service.sync_all() 
                # This also triggers analyze_transactions in sync_all?
                # Actually sync_all only does categories/customers/transactions.
                service.analyze_transactions() # Hybrid Intelligence trigger
            except Exception as e:
                print(f"❌ Webhook Sync Error for realm {realm_id}: {str(e)}")

    return {"status": "accepted"}

