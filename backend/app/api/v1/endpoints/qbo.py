from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import verify_subscription
from app.models.qbo import QBOConnection
from app.models.user import User
from app.core.config import settings
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import secrets

router = APIRouter()

@router.get("/authorize")
def authorize(user_id: str):
    try:
        # Debug: Check if settings are loaded
        print(f">>> [qbo.py] Authorize request for user: {user_id}")
        print(f">>> [qbo.py] Using Redirect URI: {settings.QBO_REDIRECT_URI}")
        print(f">>> [qbo.py] Environment: {settings.QBO_ENVIRONMENT}")
        if not settings.QBO_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Configuration Error: QBO_CLIENT_ID is missing on server.")

        auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            redirect_uri=settings.QBO_REDIRECT_URI,
            environment=settings.QBO_ENVIRONMENT,
        )
        scopes = [Scopes.ACCOUNTING]
        print(f">>> [qbo.py] Requesting Scopes: {scopes}")
        auth_url = auth_client.get_authorization_url(scopes, state_token=user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        import traceback
        print(f"Error in authorize: {str(e)}")
        # Raise generic 500 but include detail
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/debug-config")
def debug_config(user=Depends(verify_subscription)):
    return {
        "client_id_set": bool(settings.QBO_CLIENT_ID),
        "client_id_len": len(settings.QBO_CLIENT_ID) if settings.QBO_CLIENT_ID else 0,
        "redirect_uri": settings.QBO_REDIRECT_URI,
        "environment": settings.QBO_ENVIRONMENT
    }

@router.get("/callback")
def callback(code: str, state: str, realmId: str, db: Session = Depends(get_db)):
    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        redirect_uri=settings.QBO_REDIRECT_URI,
        environment=settings.QBO_ENVIRONMENT,
    )
    auth_client.get_bearer_token(code, realm_id=realmId)
    
    # State holds the user_id in this implementation
    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realmId).first()
    if not connection:
        connection = QBOConnection(user_id=user.id, realm_id=realmId)
    
    connection.refresh_token = auth_client.refresh_token
    connection.access_token = auth_client.access_token
    db.add(connection)
    db.commit()
    
    redirect_url = f"{settings.NEXT_PUBLIC_APP_URL}/dashboard?code={code}&state={state}&realmId={realmId}"
    return RedirectResponse(url=redirect_url)

from app.models.qbo import BankAccount
from app.services.transaction_service import TransactionService
from typing import List
from pydantic import BaseModel

class AccountSelectionSchema(BaseModel):
    realm_id: str
    active_account_ids: List[str]

@router.get("/accounts")
async def get_accounts(realm_id: str, db: Session = Depends(get_db), user=Depends(verify_subscription)):
    print(f"🔍 [get_accounts] Starting for realm_id: {realm_id}")
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        print(f"❌ [get_accounts] No connection found for realm_id: {realm_id}")
        return {"accounts": [], "limit": 0, "active_count": 0}
    
    print(f"✅ [get_accounts] Connection found for user: {connection.user_id}")
    
    # Ensure accounts are synced first (at least metadata)
    service = TransactionService(db, connection)
    try:
        print(f"🔄 [get_accounts] Starting sync_bank_accounts...")
        await service.sync_bank_accounts() # This syncs all without limit
        print(f"✅ [get_accounts] sync_bank_accounts completed")
    except Exception as e:
        print(f"⚠️ [get_accounts] Sync failed: {e}")
        import traceback
        print(f"📋 [get_accounts] Traceback: {traceback.format_exc()}")
        db.rollback()
        # Continue to return what we have in DB
    
    accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).order_by(BankAccount.name).all()
    print(f"📊 [get_accounts] Found {len(accounts)} accounts in database")
    
    # Determine limit
    limit = service._get_account_limit()
    
    return {
        "accounts": [
            {
                "id": a.id, 
                "name": a.name, 
                "balance": float(a.balance), 
                "is_active": a.is_active, 
                "is_connected": a.is_connected,
                "currency": a.currency
            } 
            for a in accounts
        ],
        "limit": limit,
        "active_count": len([a for a in accounts if a.is_active]),
        "tier": db.query(User).filter(User.id == connection.user_id).first().subscription_tier
    }

@router.post("/accounts/select")
async def update_account_selection(payload: AccountSelectionSchema, db: Session = Depends(get_db)):
    realm_id = payload.realm_id
    selected_ids = payload.active_account_ids
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
         raise HTTPException(status_code=404, detail="QBO Connection not found")
    
    # Verify Subscription (Manual)
    from app.api.deps import get_current_user, get_subscription_status
    user = db.query(User).filter(User.id == connection.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    status = get_subscription_status(user)
    if status in ['expired', 'no_plan']:
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "subscription_required",
                "message": "Your trial has expired. Please upgrade to a paid plan to continue.",
                "tier": user.subscription_tier
            }
        )
         
    service = TransactionService(db, connection)
    limit = service._get_account_limit()
    
    if len(selected_ids) > limit:
        raise HTTPException(status_code=402, detail=f"Selection exceeds analytics limit of {limit} accounts. Please upgrade.")
        
    all_accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).all()
    
    updated_count = 0
    for acc in all_accounts:
        is_selected = acc.id in selected_ids
        if acc.is_active != is_selected:
            acc.is_active = is_selected
            updated_count += 1
            
    db.commit()
    
    # Trigger sync if changes made
    if updated_count > 0:
        await service.sync_transactions() # Will only pick active ones
        
    return {"status": "success", "message": f"Updated {updated_count} accounts"}

@router.post("/accounts/preview")
async def preview_account_sync(payload: AccountSelectionSchema, db: Session = Depends(get_db)):
    realm_id = payload.realm_id
    selected_ids = payload.active_account_ids
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
         raise HTTPException(status_code=404, detail="QBO Connection not found")
         
    # Verify Subscription (Manual)
    from app.api.deps import get_current_user, get_subscription_status
    user = db.query(User).filter(User.id == connection.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    status = get_subscription_status(user)
    if status in ['expired', 'no_plan']:
        raise HTTPException(
            status_code=402, 
            detail="Subscription required"
        )

    # Refresh token if needed is handled by QBOClient
    from app.services.qbo_client import QBOClient
    qbo_client = QBOClient(db, connection) 

    # Fetch Transactions (Mirroring sync logic)
    total_count = 0
    matched_count = 0
    unmatched_count = 0
    account_breakdown = {acc_id: 0 for acc_id in selected_ids}

    queries = [
        "SELECT * FROM Purchase MAXRESULTS 1000",
        "SELECT * FROM Deposit MAXRESULTS 500",
        "SELECT * FROM CreditCardCredit MAXRESULTS 500",
        "SELECT * FROM JournalEntry MAXRESULTS 500",
        "SELECT * FROM Transfer MAXRESULTS 500"
    ]

    all_txs = []
    for q in queries:
        try:
            res = await qbo_client.query(q) # ASYNC await
            entity = q.split()[3]
            txs = res.get("QueryResponse", {}).get(entity, [])
            all_txs.extend(txs)
        except:
            continue

    for p in all_txs:
        # Resolve Account ID (differs by type)
        acc_id = None
        if "AccountRef" in p:
            acc_id = str(p["AccountRef"].get("value"))
        elif "DepositToAccountRef" in p:
            acc_id = str(p["DepositToAccountRef"].get("value"))
        elif "FromAccountRef" in p:
            acc_id = str(p["FromAccountRef"].get("value"))
        
        # Check if the primary account ID is selected
        if acc_id and acc_id in selected_ids:
            pass # We're good
        else:
            # Check secondary ID for Transfers (ToAccountRef)
            to_acc_id = None
            if "ToAccountRef" in p:
                to_acc_id = str(p["ToAccountRef"].get("value"))
            
            if to_acc_id and to_acc_id in selected_ids:
                acc_id = to_acc_id
            else:
                continue

        total_count += 1
        account_breakdown[acc_id] = account_breakdown.get(acc_id, 0) + 1
        
        # Determine Status
        has_linked_txn = len(p.get("LinkedTxn", [])) > 0
        
        # Check for manual categorization via TxnType
        is_manually_categorized = False
        purchase_ex = p.get("PurchaseEx", {})
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    # TxnType 54 = Manually added/categorized expense
                    if txn_type == "54":
                        is_manually_categorized = True
                        break
        
        if has_linked_txn or is_manually_categorized:
            matched_count += 1
        else:
            unmatched_count += 1

    return {
        "realm_id": realm_id,
        "selected_count": len(selected_ids),
        "total_transactions": total_count,
        "already_matched": matched_count,
        "to_analyze": unmatched_count,
        "account_breakdown": account_breakdown
    }

@router.get("/analyze")
def force_analyze(realm_id: str, tx_id: str = None, db: Session = Depends(get_db)):
    """Manual trigger for AI analysis. Can target a specific transaction for re-analysis."""
    from modal_app import process_ai_categorization
    
    if tx_id:
        print(f"🚀 [force_analyze] Resetting status and re-analyzing tx: {tx_id}")
        from app.models.qbo import Transaction
        tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == realm_id).first()
        if tx:
            tx.status = 'unmatched'
            db.commit()
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    
    print(f"🚀 [force_analyze] Spawning AI Analysis for realm: {realm_id} {'(tx: ' + tx_id + ')' if tx_id else ''}")
    process_ai_categorization.spawn(realm_id, tx_id=tx_id)
    return {"status": "success", "message": "AI analysis triggered"}

@router.delete("/disconnect")
def disconnect_qbo(realm_id: str, db: Session = Depends(get_db)):
    """
    Disconnect from QuickBooks and delete all associated data.
    This removes the connection, transactions, bank accounts, and sync logs.
    """
    print(f"🔌 [disconnect] Called with realm_id: {realm_id}")
    from app.models.qbo import Transaction, BankAccount, SyncLog, Category, Customer
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        print(f"❌ [disconnect] No connection found for realm_id: {realm_id}")
        raise HTTPException(status_code=404, detail="Connection not found")
    
    print(f"✅ [disconnect] Found connection for user: {connection.user_id}")
    
    try:
        # Revoke tokens on Intuit side first
        from app.services.qbo_client import QBOClient
        try:
            client = QBOClient(db, connection)
            client.revoke()
        except Exception as e:
            print(f"⚠️ [disconnect] Revocation failed during disconnect (continuing anyway): {e}")

        # Delete all associated data
        tx_count = db.query(Transaction).filter(Transaction.realm_id == realm_id).delete()
        acc_count = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).delete()
        log_count = db.query(SyncLog).filter(SyncLog.realm_id == realm_id).delete()
        
        print(f"🗑️ [disconnect] Deleted: {tx_count} transactions, {acc_count} accounts, {log_count} logs")
        
        # Delete the connection itself
        db.delete(connection)
        db.commit()
        
        print(f"✅ [disconnect] Successfully disconnected realm_id: {realm_id}")
        return {"status": "success", "message": "Disconnected from QuickBooks"}
    except Exception as e:
        print(f"❌ [disconnect] Error: {e}")
        import traceback
        print(f"📋 [disconnect] Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@router.get("/logs")
def get_sync_logs(realm_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the latest sync logs for debugging.
    """
    from app.models.qbo import SyncLog
    logs = db.query(SyncLog).filter(SyncLog.realm_id == realm_id).order_by(SyncLog.timestamp.desc()).limit(20).all()
    return [{
        "timestamp": log.timestamp,
        "entity": log.entity_type,
        "op": log.operation,
        "count": log.count,
        "status": log.status,
        "details": log.details
    } for log in logs]
