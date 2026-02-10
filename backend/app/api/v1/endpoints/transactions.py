from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.db.session import get_db
from app.api.deps import verify_subscription
from app.models.qbo import QBOConnection, Transaction, TransactionSplit, Category
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
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    payee: Optional[str] = None

class TransactionSchema(BaseModel):
    id: str
    date: datetime
    description: Optional[str] = None
    amount: float
    currency: str
    transaction_type: Optional[str] = None
    note: Optional[str] = None
    tags: List[str] = []
    suggested_tags: List[str] = []
    status: str
    suggested_category_id: Optional[str] = None
    suggested_category_name: Optional[str] = None
    suggested_payee: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
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
    payee: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    sync_token: Optional[str] = None

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
async def sync_user_transactions(realm_id: str, db: Session = Depends(get_db), user=Depends(verify_subscription)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    try:
        from modal_app import sync_user_data
        sync_user_data.spawn(realm_id)
        return {"message": "Background sync triggered successfully"}
    except (ImportError, Exception):
        # Fallback to local async sync
        from app.services.sync_service import SyncService
        service = SyncService(db, connection)
        await service.sync_all()
        return {"message": "Sync completed (local async fallback)"}

@router.post("/{tx_id}/split")
def split_transaction(realm_id: str, tx_id: str, splits: List[SplitSchema], db: Session = Depends(get_db), user=Depends(verify_subscription)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Calculate total and validate against tx.amount
    total_split = sum(s.amount for s in splits)
    if abs(total_split - tx.amount) > 0.01:
        raise HTTPException(status_code=400, detail=f"Split total ({total_split}) must match transaction amount ({tx.amount})")
    
    # Clear existing splits
    db.query(TransactionSplit).filter(TransactionSplit.transaction_id == tx_id).delete()
    
    # Create new splits
    tx.is_split = True
    for s in splits:
        split = TransactionSplit(
            transaction_id=tx.id,
            category_name=s.category_name,
            amount=s.amount,
            description=s.description or tx.description
        )
        # Resolve category ID if possible
        cat = db.query(Category).filter(Category.name == s.category_name, Category.realm_id == realm_id).first()
        if cat:
            split.category_id = cat.id
            
        db.add(split)
    
    tx.status = 'pending_approval'
    db.commit()
    return {"message": "Transaction split successfully", "splits_count": len(splits)}

@router.post("/analyze")
def analyze_user_transactions(realm_id: str, tx_id: str = None, db: Session = Depends(get_db), user=Depends(verify_subscription)):
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
        process_ai_categorization.spawn(realm_id, tx_id=tx_id, allow_ai=True)
        
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
async def approve_transaction(realm_id: str, tx_id: str, db: Session = Depends(get_db), user=Depends(verify_subscription)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    service = TransactionService(db, connection)
    try:
        # 1. Optimistic local update
        result = await service.approve_transaction(tx_id, optimistic=True)
        
        # 2. Spawn background QBO sync
        try:
            from modal_app import process_single_approval
            process_single_approval.spawn(realm_id, tx_id)
        except (ImportError, Exception) as e:
            print(f"⚠️ [API] Background worker spawn failed. Running synchronously as fallback: {e}")
            # Optional: Fallback to sync if Modal isn't available
            # await service.sync_approved_to_qbo(tx_id)
            pass

        return {"message": "Transaction approval queued", "tx_id": tx_id}
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
    if update.category_id is not None:
        tx.category_id = update.category_id
        tx.category_name = update.category_name or tx.category_name
        if tx.status == 'approved':
             tx.status = 'pending_approval'
    if update.payee is not None:
        tx.payee = update.payee
        if tx.status == 'approved':
             tx.status = 'pending_approval'
        
    db.commit()
    db.refresh(tx)
    return tx

@router.post("/upload-receipt")
def upload_receipt(
    realm_id: str,
    tx_id: Optional[str] = Query(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(verify_subscription)
):
    try:
        # Receipt upload remains sync/threaded for file IO
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail="QBO Connection not found")
        
        # Use /tmp for ephemeral storage (works in Modal/Lambda)
        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sanitize filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
        file_path = os.path.join(upload_dir, f"{realm_id}_{safe_filename}")
        
        print(f"📂 [Upload] Saving to {file_path}")
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
        
        mime_type = file.content_type or "image/jpeg"
        print(f"📊 [Upload] Detected MIME: {mime_type}")
        
        try:
            print("🚀 [Upload] Triggering Modal analysis...")
            from modal_app import process_receipt_modal
            
            result = process_receipt_modal.remote(realm_id, content, file.filename, mime_type=mime_type)
            
            if "error" in result:
                 raise Exception(result["error"])
                 
        except ImportError:
            print("⚠️ Modal not found, running locally")
            service = ReceiptService(db, realm_id)
            result_obj = service.process_receipt(content, file.filename, mime_type=mime_type)
            match = result_obj.get('match')
            result = {
                "extracted": result_obj.get('extracted'),
                "match_id": match.id if match else None
            }
        except Exception as e:
            print(f"❌ Serverless Receipt Error: {e}")
            # Fallback to local
            service = ReceiptService(db, realm_id)
            result_obj = service.process_receipt(content, file.filename, mime_type=mime_type)
            match = result_obj.get('match')
            result = {
                "extracted": result_obj.get('extracted'),
                "match_id": match.id if match else None
            }

        match_id = tx_id or result.get('match_id')
        extracted = result.get('extracted')
        
        # If manual tx_id was provided, ensure it's updated (service might not have found it if provided manually)
        if tx_id:
            match = db.query(Transaction).filter(Transaction.id == tx_id).first()
            if match:
                match.receipt_url = file_path
                match.receipt_content = content
                match.receipt_data = extracted
                db.add(match)
                db.commit()

        return {
            "message": "Receipt processed",
            "extracted": extracted,
            "match_id": match_id,
            "receipt_url": file_path  # Return the file path for UI update
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Upload Endpoint Crash: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload Error: {str(e)}")



@router.post("/bulk-approve")
async def bulk_approve_transactions(realm_id: str, tx_ids: List[str], db: Session = Depends(get_db), user=Depends(verify_subscription)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    try:
        from modal_app import bulk_approve_modal
        # Spawn background task
        bulk_approve_modal.spawn(realm_id, tx_ids)
        return {"message": "Bulk approval started in background", "count": len(tx_ids)}
    except ImportError:
        print("⚠️ Modal not found, falling back to local bulk approve")
        service = TransactionService(db, connection)
        results = await service.bulk_approve(tx_ids)
        return {"results": results, "mode": "local_fallback"}
    except Exception as e:
        print(f"❌ Modal Spawn Error: {e}")
        # Fallback
        service = TransactionService(db, connection)
        results = await service.bulk_approve(tx_ids)
        return {"results": results, "mode": "local_fallback_error"}
