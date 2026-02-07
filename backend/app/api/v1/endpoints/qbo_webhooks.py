from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
import hashlib
import hmac
import base64
from app.core.config import settings

router = APIRouter()

from app.services.transaction_service import TransactionService
from app.services.analysis_service import AnalysisService
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
            print(f"🔄 [Webhook] Triggering background sync for realm {realm_id}")
            try:
                from modal_app import sync_user_data
                sync_user_data.spawn(realm_id)
            except ImportError:
                print("⚠️ [Webhook] Modal not found, falling back to local sync")
                try:
                    sync_service = TransactionService(db, connection)
                    await sync_service.sync_transactions() # Use async wrapper if available or sync
                    
                    # Hybrid Intelligence trigger
                    analysis_service = AnalysisService(db, realm_id)
                    analysis_service.analyze_transactions()
                except Exception as e:
                    print(f"❌ Webhook Local Sync Error for realm {realm_id}: {str(e)}")
            except Exception as e:
                print(f"❌ Webhook Modal Spawn Error for realm {realm_id}: {str(e)}")

    return {"status": "accepted"}

