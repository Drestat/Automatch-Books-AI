import modal
import os
from dotenv import dotenv_values
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-unexpected-for-review")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_unexpected():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    from app.core.feed_logic import FeedLogic
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # The 3 unexpected transactions
    targets = [
        {"name": "Tania's Nursery", "amount": 54.92, "date": "2025-12-22"},
        {"name": "Hicks Hardware", "amount": 42.40, "date": "2026-01-07"},
        {"name": "Lee Advertising", "amount": 74.86, "date": "2025-12-30"}
    ]
    
    print(f"\n{'='*120}")
    print(f"INVESTIGATING UNEXPECTED 'FOR REVIEW' TRANSACTIONS")
    print(f"{'='*120}\n")
    
    for target in targets:
        tx = session.query(Transaction).filter(
            Transaction.description.ilike(f"%{target['name']}%"),
            Transaction.amount == target['amount']
        ).first()
        
        if not tx:
            print(f"❌ {target['name']} NOT FOUND")
            continue
        
        print(f"\n{'─'*120}")
        print(f"🔍 {target['name']} (${target['amount']})")
        print(f"{'─'*120}")
        
        raw = tx.raw_json
        
        # Extract signals
        txn_type = "Unknown"
        if "PurchaseEx" in raw and "any" in raw["PurchaseEx"]:
            for item in raw["PurchaseEx"]["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
        
        sync_token = raw.get("SyncToken", "0")
        doc_number = raw.get("DocNumber")
        
        # Check LinkedTxn
        has_linked = False
        linked_details = []
        for line in raw.get("Line", []):
            if "LinkedTxn" in line and line["LinkedTxn"]:
                has_linked = True
                for link in line["LinkedTxn"]:
                    linked_details.append(f"{link.get('TxnType')} #{link.get('TxnId')}")
        
        # Check category
        category = None
        for line in raw.get("Line", []):
            if "AccountBasedExpenseLineDetail" in line:
                account_ref = line["AccountBasedExpenseLineDetail"].get("AccountRef", {})
                category = account_ref.get("name")
        
        # Run through FeedLogic
        is_matched, reason = FeedLogic.analyze(raw)
        
        print(f"  Database ID: {tx.id}")
        print(f"  QBO ID: {raw.get('Id')}")
        print(f"  Date: {tx.date}")
        print(f"  Amount: ${tx.amount}")
        print(f"  Description: {tx.description}")
        print(f"\n  📊 TECHNICAL SIGNALS:")
        print(f"  ├─ TxnType: {txn_type}")
        print(f"  ├─ SyncToken: {sync_token}")
        print(f"  ├─ DocNumber: {doc_number}")
        print(f"  ├─ LinkedTxn: {has_linked}")
        if linked_details:
            print(f"  │  └─ Links: {', '.join(linked_details)}")
        print(f"  └─ Category: {category}")
        
        print(f"\n  🧠 FEEDLOGIC ANALYSIS:")
        print(f"  ├─ Result: {'CATEGORIZED' if is_matched else 'FOR REVIEW'}")
        print(f"  └─ Reason: {reason}")
        
        print(f"\n  💾 DATABASE STATUS:")
        print(f"  └─ is_qbo_matched: {tx.is_qbo_matched} ({'CATEGORIZED' if tx.is_qbo_matched else 'FOR REVIEW'})")
        
        # Show relevant raw JSON
        print(f"\n  📄 RAW JSON (Key Fields):")
        key_fields = {
            "Id": raw.get("Id"),
            "TxnDate": raw.get("TxnDate"),
            "SyncToken": raw.get("SyncToken"),
            "DocNumber": raw.get("DocNumber"),
            "EntityRef": raw.get("EntityRef"),
            "Line": raw.get("Line", [])[:1]  # Just first line
        }
        print(f"  {json.dumps(key_fields, indent=2)}")

if __name__ == "__main__":
    pass
