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
async def sync_user_transactions(realm_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    try:
        # Prefer Modal for heavy lifting if configured
        try:
            from modal_app import sync_user_data
            # Modal spawn is sync (fire and forget hook), but we can await it if the client library supports it, 
            # usually .spawn() is non-blocking or fast.
            # If we want to force local async sync:
            # raise ImportError 
            sync_user_data.spawn(realm_id)
            return {"message": "Background sync triggered successfully"}
        except (ImportError, Exception):
            # Fallback to local async sync
            service = TransactionService(db, connection)
            await service.sync_all()
            return {"message": "Sync completed (local async fallback)"}
    except Exception as e:
        return {"message": "Sync failed", "error": str(e)}

@router.post("/analyze")
def analyze_user_transactions(realm_id: str, tx_id: str = None, db: Session = Depends(get_db)):
    # Keep analysis sync/threaded for now unless we refactor AnalysisService too.
    # AnalysisService relies on AI/DB, usually blocking.
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

        # Check Tokens synchronously BEFORE dispatching to Modal
        from app.services.token_service import TokenService
        token_service = TokenService(db)
        
        # Estimate cost (1 token per tx)
        cost = 1
        if not token_service.has_sufficient_tokens(connection.user_id, cost):
            raise HTTPException(status_code=402, detail="Insufficient tokens. Please upgrade your plan.")

        from modal_app import process_ai_categorization
        process_ai_categorization.spawn(realm_id, tx_id=tx_id)
        
        # Deduct synchronously to update UI immediately? 
        # Ideally the async task does it to ensure uniqueness, but doing it here prevents "free" spamming 
        # while waiting for async. 
        # Let's deduct here for the immediate endpoint usage (re-analyze).
        token_service.deduct_tokens(connection.user_id, cost, reason=f"AI Analysis Request: {tx_id}")

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
async def approve_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    try:
        result = await service.approve_transaction(tx_id)
        return {"message": "Transaction approved and synced to QBO", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{tx_id}", response_model=TransactionSchema)
def update_transaction(realm_id: str, tx_id: str, update: TransactionUpdate, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if update.note is not None:
        tx.note = update.note
    if update.tags is not None:
        tx.tags = update.tags
    if update.suggested_category_id is not None:
        tx.suggested_category_id = update.suggested_category_id
        tx.suggested_category_name = update.suggested_category_name or tx.suggested_category_name
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
    # Receipt upload remains sync/threaded for file IO
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{realm_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    from app.services.token_service import TokenService
    
    token_service = TokenService(db)
    receipt_cost = 5
    
    if not token_service.has_sufficient_tokens(connection.user_id, receipt_cost):
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
        result = process_receipt_modal.remote(realm_id, content, file.filename)
        
        if "error" in result:
             raise Exception(result["error"])
             
    except ImportError:
        print("⚠️ Modal not found, running locally")
        service = ReceiptService(db, realm_id)
        result_obj = service.process_receipt(content, file.filename)
        match = result_obj.get('match')
        result = {
            "extracted": result_obj.get('extracted'),
            "match_id": match.id if match else None
        }
    except Exception as e:
        print(f"❌ Serverless Receipt Error: {e}")
        service = ReceiptService(db, realm_id)
        result_obj = service.process_receipt(content, file.filename)
        match = result_obj.get('match')
        result = {
            "extracted": result_obj.get('extracted'),
            "match_id": match.id if match else None
        }

    match_id = result.get('match_id')
    extracted = result.get('extracted')
    
    match = None
    if match_id:
        match = db.query(Transaction).filter(Transaction.id == match_id).first()
        if match:
            match.receipt_url = file_path 
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
async def bulk_approve_transactions(realm_id: str, tx_ids: List[str], db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    results = await service.bulk_approve(tx_ids) # Now async
    return {"results": results}
