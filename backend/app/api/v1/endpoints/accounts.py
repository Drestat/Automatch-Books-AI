from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.models.qbo import BankAccount, Category, Tag, Transaction, QBOConnection
from typing import List, Optional
from pydantic import BaseModel
import uuid
from app.services.qbo_client import QBOClient

router = APIRouter()

# --- Schemas ---

class BankAccountSchema(BaseModel):
    id: str
    name: str
    nickname: Optional[str] = None
    currency: str
    balance: float

    class Config:
        from_attributes = True

class BankAccountUpdate(BaseModel):
    nickname: str

class TagSchema(BaseModel):
    id: str
    name: str
    qbo_tag_id: Optional[str] = None

    class Config:
        from_attributes = True

class TagCreate(BaseModel):
    name: str

class CategorySchema(BaseModel):
    id: str
    name: str
    type: str

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/accounts", response_model=List[BankAccountSchema])
def get_bank_accounts(realm_id: str, db: Session = Depends(get_db)):
    """Returns list of Bank Accounts with Nicknames"""
    # First try the new table
    accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).all()
    
    # Fallback to Transaction distinct query if table is empty (migration safety)
    if not accounts:
        # TODO: Trigger background sync if empty? For now, return empty or fallback
        pass
        
    return accounts

@router.patch("/accounts/{account_id}", response_model=BankAccountSchema)
def update_bank_nickname(realm_id: str, account_id: str, update: BankAccountUpdate, db: Session = Depends(get_db)):
    """Updates the nickname of a bank account"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id, 
        BankAccount.realm_id == realm_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.nickname = update.nickname
    db.commit()
    db.refresh(account)
    return account

@router.get("/tags", response_model=List[TagSchema])
def get_tags(realm_id: str, db: Session = Depends(get_db)):
    """Returns list of Tags"""
    return db.query(Tag).filter(Tag.realm_id == realm_id).all()

@router.post("/tags", response_model=TagSchema)
def create_tag(realm_id: str, tag_in: TagCreate, db: Session = Depends(get_db)):
    """Creates a new tag (Local + QBO Sync)"""
    # 1. Create locally
    new_tag = Tag(
        realm_id=realm_id, 
        name=tag_in.name
    )
    
    # 2. Try to sync to QBO (Best Effort)
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if connection:
            pass # TODO: Implement QBO Tag Create API call if supported
            # client = QBOClient(db, connection)
            # data = client.request("POST", "tag", json_payload={"Name": tag_in.name})
            # new_tag.qbo_tag_id = data["Id"]
    except Exception as e:
        print(f"Warning: Failed to sync tag to QBO: {e}")
        
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@router.get("/categories", response_model=List[CategorySchema])
def get_categories(realm_id: str, db: Session = Depends(get_db)):
    """Returns list of Expense Categories"""
    return db.query(Category).filter(
        Category.realm_id == realm_id,
        Category.type.in_(['Expense', 'Cost of Goods Sold', 'Other Expense'])
    ).order_by(Category.name).all()
