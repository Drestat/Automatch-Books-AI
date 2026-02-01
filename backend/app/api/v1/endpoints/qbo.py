from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
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
            return {"error": "Configuration Error: QBO_CLIENT_ID is missing on server."}

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
        return {"error": f"Internal Server Error: {str(e)}", "trace": traceback.format_exc()}

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
def get_accounts(realm_id: str, db: Session = Depends(get_db)):
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        return {"accounts": [], "limit": 0, "active_count": 0}
    
    # Ensure accounts are synced first (at least metadata)
    service = TransactionService(db, connection)
    try:
        service.sync_bank_accounts() # This syncs all without limit
    except Exception as e:
        print(f"⚠️ [get_accounts] Sync failed: {e}")
        # Continue to return what we have in DB
    
    accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).order_by(BankAccount.name).all()
    
    # Determine limit
    limit = service._get_account_limit()
    
    return {
        "accounts": [
            {
                "id": a.id, 
                "name": a.name, 
                "balance": float(a.balance), 
                "is_active": a.is_active, 
                "currency": a.currency
            } 
            for a in accounts
        ],
        "limit": limit,
        "active_count": len([a for a in accounts if a.is_active]),
        "tier": db.query(User).filter(User.id == connection.user_id).first().subscription_tier
    }

@router.post("/accounts/select")
def update_account_selection(payload: AccountSelectionSchema, db: Session = Depends(get_db)):
    realm_id = payload.realm_id
    selected_ids = payload.active_account_ids
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
         raise HTTPException(status_code=404, detail="QBO Connection not found")
         
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
        service.sync_transactions() # Will only pick active ones
        
    return {"status": "success", "updated": updated_count}

@router.delete("/disconnect")
def disconnect_qbo(realm_id: str, db: Session = Depends(get_db)):
    """
    Disconnect from QuickBooks and delete all associated data.
    This removes the connection, transactions, bank accounts, and sync logs.
    """
    from app.models.qbo import Transaction, BankAccount, SyncLog, Category, Customer
    
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Delete all associated data
        db.query(Transaction).filter(Transaction.realm_id == realm_id).delete()
        db.query(BankAccount).filter(BankAccount.realm_id == realm_id).delete()
        db.query(SyncLog).filter(SyncLog.realm_id == realm_id).delete()
        
        # Delete the connection itself
        db.delete(connection)
        db.commit()
        
        return {"status": "success", "message": "Disconnected from QuickBooks"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

