from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.qbo import Transaction, QBOConnection
from app.services.sync_service import SyncService
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SplitSchema(BaseModel):
    category_name: str
    amount: float
    description: str = None

    class Config:
        from_attributes = True

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
    is_split: bool = False
    splits: List[SplitSchema] = []

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

from fastapi import File, UploadFile
import os
import shutil

@router.post("/upload-receipt")
def upload_receipt(
    realm_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    # Save file locally
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{realm_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process with AI
    with open(file_path, "rb") as f:
        content = f.read()
    
    sync_service = SyncService(db, connection)
    result = sync_service.process_receipt(content, file.filename)
    
    # If match found, update the transaction
    match = result.get('match')
    if match:
        match.receipt_url = file_path 
        match.receipt_data = result.get('extracted')
        db.add(match)
        db.commit()
    
    return {
        "message": "Receipt processed",
        "extracted": result.get('extracted'),
        "match_id": match.id if match else None
    }
