import modal
import os
from dotenv import dotenv_values
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-for-review")
config = dotenv_values(os.path.join(base_dir, ".env"))
qbo_secrets = modal.Secret.from_dict({
    "DATABASE_URL": config.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": config.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": config.get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": config.get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": config.get("QBO_REDIRECT_URI", "")
})

@app.function(image=image, secrets=[qbo_secrets])
def inspect_for_review_txns():
    """
    Inspects the specific transactions shown in the user's screenshot
    to identify what signals indicate "match suggestions"
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User
    from app.models.qbo import QBOConnection, Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # The 5 transactions from the screenshot
    targets = [
        "Bob's Burger",
        "Norton Lumber",
        "Squeaky Kleen",
        "Tania's Nursery"
    ]
    
    print(f"\n{'='*120}")
    print(f"INSPECTING 'FOR REVIEW' TRANSACTIONS FROM SCREENSHOT")
    print(f"{'='*120}\n")
    
    for target in targets:
        txs = session.query(Transaction).filter(
            Transaction.description.ilike(f"%{target}%")
        ).all()
        
        print(f"\n{'─'*120}")
        print(f"🔍 {target}")
        print(f"{'─'*120}")
        
        for tx in txs:
            raw = tx.raw_json
            
            # Extract key signals
            txn_type = "Unknown"
            if "PurchaseEx" in raw and "any" in raw["PurchaseEx"]:
                for item in raw["PurchaseEx"]["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
            
            sync_token = raw.get("SyncToken", "0")
            doc_number = raw.get("DocNumber")
            
            # Check for LinkedTxn
            has_linked = False
            for line in raw.get("Line", []):
                if "LinkedTxn" in line and line["LinkedTxn"]:
                    has_linked = True
                    break
            
            # Check for match suggestions (look for specific fields)
            has_vendor_ref = "VendorRef" in raw or "EntityRef" in raw
            has_account_ref = any("AccountRef" in line.get("AccountBasedExpenseLineDetail", {}) 
                                 for line in raw.get("Line", []))
            
            print(f"  ID: {tx.id}")
            print(f"  Date: {tx.date}")
            print(f"  Amount: ${tx.amount}")
            print(f"  TxnType: {txn_type}")
            print(f"  SyncToken: {sync_token}")
            print(f"  DocNumber: {doc_number}")
            print(f"  LinkedTxn: {has_linked}")
            print(f"  VendorRef/EntityRef: {has_vendor_ref}")
            print(f"  AccountRef: {has_account_ref}")
            print(f"  DB Status: {'CATEGORIZED' if tx.is_qbo_matched else 'FOR REVIEW'}")
            print(f"\n  Raw JSON Preview:")
            print(f"  {json.dumps(raw, indent=2)[:500]}...")
            print()

if __name__ == "__main__":
    pass
