from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.models.qbo import Transaction
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class AccountSchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AccountSchema])
def get_accounts(realm_id: str, db: Session = Depends(get_db)):
    """
    Returns a distinct list of bank accounts found in the transaction history.
    This mirrors the accounts present in the data lake.
    """
    # Query distinct account_id and account_name
    # Note: We rely on account_id as the primary key for filtering
    results = db.query(Transaction.account_id, Transaction.account_name)\
                .filter(Transaction.realm_id == realm_id)\
                .distinct().all()
    
    accounts = []
    seen_ids = set()
    
    for row in results:
        # Handle potential None values or duplicates if ID is missing (shouldn't happen in QBO data but good to be safe)
        if row.account_id and row.account_id not in seen_ids:
            accounts.append(AccountSchema(id=row.account_id, name=row.account_name or "Unknown Account"))
            seen_ids.add(row.account_id)
            
    return accounts
