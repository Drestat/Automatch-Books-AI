from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

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

class TransactionUpdate(BaseModel):
    note: Optional[str] = None
    tags: Optional[List[str]] = None
    suggested_category_id: Optional[str] = None
    suggested_category_name: Optional[str] = None

class TransactionSchema(BaseModel):
    id: str
    date: datetime
    description: str
    amount: float
    currency: str
    transaction_type: Optional[str] = None
    note: Optional[str] = None
    tags: List[str] = []
    suggested_tags: List[str] = []
    status: str
    suggested_category_name: Optional[str] = None
    reasoning: Optional[str] = None
    vendor_reasoning: Optional[str] = None
    category_reasoning: Optional[str] = None
    note_reasoning: Optional[str] = None
    tax_deduction_note: Optional[str] = None
    confidence: Optional[float] = None
    is_qbo_matched: bool = False
    is_excluded: bool = False
    is_bank_feed_import: bool = True
    forced_review: bool = False
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
        if tx_id:
            tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
            if tx and tx.is_qbo_matched:
                tx.forced_review = True
                db.add(tx)
                db.commit()

        from modal_app import process_ai_categorization
        process_ai_categorization.spawn(realm_id, tx_id=tx_id)
        return {"message": f"AI categorization {'for ' + tx_id if tx_id else ''} triggered successfully"}
    except Exception as e:
        if tx_id:
            tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
            if tx and tx.is_qbo_matched:
                tx.forced_review = True
                db.add(tx)
                db.commit()
        
        service = AnalysisService(db, realm_id)
        try:
            results = service.analyze_transactions(tx_id=tx_id)
            return {"message": "AI analysis completed (synchronous fallback)", "count": len(results) if isinstance(results, list) else 0}
        except Exception as inner_e:
             return {"message": "AI analysis failed", "error": str(inner_e)}

@router.post("/{tx_id}/exclude")
def exclude_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.is_excluded = True
    db.commit()
    return {"message": "Transaction excluded"}

@router.post("/{tx_id}/include")
def include_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.is_excluded = False
    db.commit()
    return {"message": "Transaction included"}

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

@router.patch("/{tx_id}", response_model=TransactionSchema)
def update_transaction(realm_id: str, tx_id: str, update: TransactionUpdate, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # We update fields if they are explicitly sent (even empty strings or lists)
    # But checks for None to respect partial updates
    if update.note is not None:
        tx.note = update.note
    if update.tags is not None:
        tx.tags = update.tags
    if update.suggested_category_id is not None:
        tx.suggested_category_id = update.suggested_category_id
        tx.suggested_category_name = update.suggested_category_name or tx.suggested_category_name
        # Reset approval status if category changes
        if tx.status == 'approved':
             tx.status = 'pending_approval'
        
    db.commit()
    db.refresh(tx)
    return tx

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
    
    # Process with AI (Serverless)
    from app.services.token_service import TokenService
    
    token_service = TokenService(db)
    receipt_cost = 5
    
    if not token_service.has_sufficient_tokens(connection.user_id, receipt_cost):
        # Clean up file
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=402, detail="Insufficient tokens for receipt scan (Cost: 5 tokens)")
    
    token_service.deduct_tokens(connection.user_id, receipt_cost, reason="Receipt Scan")

    with open(file_path, "rb") as f:
        content = f.read()
    
    try:
        from modal_app import process_receipt_modal
        # Execute remotely on Modal infrastructure
        result = process_receipt_modal.remote(realm_id, content, file.filename)
        
        if "error" in result:
             raise Exception(result["error"])
             
    except ImportError:
        # Fallback for local dev without Modal
        print("⚠️ Modal not found, running locally")
        service = ReceiptService(db, realm_id)
        result_obj = service.process_receipt(content, file.filename)
        # Manually serialize to match Modal output
        match = result_obj.get('match')
        result = {
            "extracted": result_obj.get('extracted'),
            "match_id": match.id if match else None
        }
    except Exception as e:
        print(f"❌ Serverless Receipt Error: {e}")
        # Fallback to local
        service = ReceiptService(db, realm_id)
        result_obj = service.process_receipt(content, file.filename)
        match = result_obj.get('match')
        result = {
            "extracted": result_obj.get('extracted'),
            "match_id": match.id if match else None
        }

    # If match found, update the transaction (Local DB update)
    match_id = result.get('match_id')
    extracted = result.get('extracted')
    
    match = None
    if match_id:
        match = db.query(Transaction).filter(Transaction.id == match_id).first()
        if match:
            match.receipt_url = file_path # Local path (or S3 in future)
            match.receipt_data = extracted
            db.add(match)
            db.commit()
            db.refresh(match)
    
    return {
        "message": "Receipt processed",
        "extracted": extracted,
        "match_id": match_id
    }

@router.post("/bulk-approve")
def bulk_approve_transactions(realm_id: str, tx_ids: List[str], db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    results = service.bulk_approve(tx_ids)
    return {"results": results}
