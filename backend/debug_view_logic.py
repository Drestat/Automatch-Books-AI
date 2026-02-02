import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi", 
        "uvicorn", 
        "psycopg2-binary", 
        "pydantic-settings", 
        "python-dotenv",
        "sqlalchemy",
        "intuit-oauth",
        "requests",
        "pytz"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

app = modal.App("debug-view-logic")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def debug_logic():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    from datetime import datetime, timezone, timedelta
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    txs = db.query(Transaction).all()
    print(f"DEBUGGING LOGIC FOR {len(txs)} TRANSACTIONS")
    print("="*120)
    print(f"{'Desc':<25} | {'Sugg. Cat':<30} | {'is_uncat':<8} | {'Date':<10} | {'is_recent':<9} | {'FINAL STATUS'}")
    print("="*120)
    # DEFINE SCHEMA LOCALLY TO TEST SERIALIZATION
    from pydantic import BaseModel
    from typing import List, Optional
    from datetime import datetime

    class SplitSchema(BaseModel):
        category_name: str
        amount: float
        description: Optional[str] = None
        class Config:
            from_attributes = True

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
        forced_review: bool = False
        is_split: bool = False
        splits: List[SplitSchema] = []
        class Config:
            from_attributes = True

    print("="*120)
    print("TESTING PYDANTIC SERIALIZATION")
    print("="*120)
    
    # EXACT LOGIC COPY FROM transactions.py
    now_utc = datetime.now(timezone.utc)
    cutoff_date = now_utc - timedelta(days=90)
    
    for tx in txs:
        # 1. Determine Logic
        expense_acc_name = (tx.suggested_category_name or "").lower()
        is_uncategorized_account = (
            "uncategorized" in expense_acc_name 
            or "ask my accountant" in expense_acc_name
            or not tx.suggested_category_name
        )
        
        if is_uncategorized_account:
            tx.status = "NEEDS_REVIEW"
        else:
            tx.status = "CATEGORIZED"
            
        # DEBUG INJECTION (Simulate it)
        tx.reasoning = (tx.reasoning or "") + f" [DBG: Cat='{tx.suggested_category_name}' Status={tx.status}]"

        # TRY VALIDATION
        try:
            schema = TransactionSchema.model_validate(tx)
            print(f"✅ Serialized: {tx.description[:15]} -> Status: {schema.status}")
        except Exception as e:
            print(f"❌ SERIALIZATION ERROR for {tx.description}: {e}")

if __name__ == "__main__":
    pass
