from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.qbo import Transaction, QBOConnection
from app.services.sync_service import SyncService
from pydantic import BaseModel
from typing import List

router = APIRouter()

class TransactionSchema(BaseModel):
    id: str
    date: str
    description: str
    amount: float
    currency: str
    status: str
    suggested_category_name: str = None
    reasoning: str = None
    confidence: float = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[TransactionSchema])
def get_transactions(realm_id: str, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.realm_id == realm_id).all()
    # Convert date to string for schema
    for tx in txs:
        tx.date = tx.date.strftime("%Y-%m-%d")
    return txs

@router.post("/sync")
def sync_user_transactions(realm_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    try:
        from modal_app import sync_user_data
        sync_user_data.spawn(realm_id)
        return {"message": "Background sync triggered successfully"}
    except Exception as e:
        # Fallback to synchronous sync if Modal is not configured or fails
        sync_service = SyncService(db, connection)
        sync_service.sync_all()
        return {"message": "Sync completed (synchronous fallback)", "error": str(e)}

@router.post("/analyze")
def analyze_user_transactions(realm_id: str, tx_id: str = None, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    try:
        from modal_app import process_ai_categorization
        process_ai_categorization.spawn(realm_id, tx_id=tx_id)
        return {"message": f"AI categorization {'for ' + tx_id if tx_id else ''} triggered successfully"}
    except Exception as e:
        sync_service = SyncService(db, connection)
        results = sync_service.analyze_transactions(tx_id=tx_id)
        return {"message": "AI analysis completed (synchronous fallback)", "count": len(results) if isinstance(results, list) else 0, "error": str(e)}

@router.post("/{tx_id}/approve")
def approve_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    sync_service = SyncService(db, connection)
    try:
        result = sync_service.approve_transaction(tx_id)
        return {"message": "Transaction approved and synced to QBO", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
