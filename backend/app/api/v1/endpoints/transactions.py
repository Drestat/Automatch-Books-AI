from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from app.api.v1.endpoints.qbo import get_db
from app.models.qbo import QBOConnection, Transaction
from app.services.transaction_service import TransactionService
from app.services.analysis_service import AnalysisService
from app.services.receipt_service import ReceiptService
from pydantic import BaseModel

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
def get_transactions(
    realm_id: str, 
    account_ids: Optional[str] = Query(None, description="Comma-separated list of account IDs"),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.realm_id == realm_id)
    
    if account_ids:
        acc_id_list = account_ids.split(",")
        query = query.filter(Transaction.account_id.in_(acc_id_list))
        
    txs = query.all()
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
        service = TransactionService(db, connection)
        service.sync_all()
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
        service = AnalysisService(db, realm_id)
        try:
            results = service.analyze_transactions(tx_id=tx_id)
            return {"message": "AI analysis completed (synchronous fallback)", "count": len(results) if isinstance(results, list) else 0}
        except Exception as inner_e:
             return {"message": "AI analysis failed", "error": str(inner_e)}

@router.post("/{tx_id}/approve")
def approve_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    try:
        result = service.approve_transaction(tx_id)
        return {"message": "Transaction approved and synced to QBO", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    service = ReceiptService(db, realm_id)
    result = service.process_receipt(content, file.filename)
    
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

@router.post("/bulk-approve")
def bulk_approve_transactions(realm_id: str, tx_ids: List[str], db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    results = service.bulk_approve(tx_ids)
    return {"results": results}
