"""
Test the filter logic on actual QBO data to see why it's not working
"""
import modal
import os
from dotenv import dotenv_values
from modal import Image

base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

image = Image.debian_slim(python_version="3.9").pip_install(
    "requests",
    "intuit-oauth",
    "python-dotenv",
    "pydantic-settings"
).add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")

app = modal.App("test-filter")

secrets = modal.Secret.from_dict({
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def test_filter_logic():
    """Test the filter on real QBO data"""
    from app.db.session import get_db
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    from datetime import datetime, timezone
    
    db = next(get_db())
    try:
        connection = db.query(QBOConnection).first()
        client = QBOClient(db, connection)
        
        # Get Mastercard purchases
        res = client.query("SELECT * FROM Purchase WHERE AccountRef = '41'")
        purchases = res.get("QueryResponse", {}).get("Purchase", [])
        
        print(f"\n{'='*100}")
        print(f"TESTING FILTER LOGIC ON {len(purchases)} MASTERCARD PURCHASES")
        print(f"{'='*100}\n")
        
        passed = []
        filtered = []
        
        for p in purchases:
            pid = p.get("Id")
            
            # Extract filter variables (EXACTLY as in the code)
            entity_ref_check = p.get("EntityRef")
            private_note_check = p.get("PrivateNote")
            doc_number_check = p.get("DocNumber")
            metadata_check = p.get("MetaData", {})
            create_time_check = metadata_check.get("CreateTime", "")
            
            # Check if created today
            is_created_today_check = False
            if create_time_check:
                try:
                    create_dt_check = datetime.fromisoformat(create_time_check.replace('Z', '+00:00'))
                    now_check = datetime.now(timezone.utc)
                    if (now_check - create_dt_check).total_seconds() < 86400:
                        is_created_today_check = True
                except: pass
            
            # Check for LinkedTxn
            has_linked_txn_check = False
            if "Line" in p:
                for line in p["Line"]:
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        has_linked_txn_check = True
                        break
            
            # Apply filter
            has_payee_check = entity_ref_check is not None
            has_note_check = private_note_check and len(private_note_check.strip()) > 0
            is_debit_check = doc_number_check and doc_number_check.lower() == "debit"
            is_bank_signal_check = is_created_today_check or has_linked_txn_check or has_payee_check or has_note_check or is_debit_check
            
            result = {
                "id": pid,
                "date": p.get("TxnDate"),
                "amount": p.get("TotalAmt"),
                "payee": entity_ref_check.get("name") if entity_ref_check else None,
                "note": private_note_check,
                "doc_num": doc_number_check,
                "created": create_time_check,
                "has_payee": has_payee_check,
                "has_note": has_note_check,
                "has_link": has_linked_txn_check,
                "is_debit": is_debit_check,
                "is_today": is_created_today_check,
                "PASSES": is_bank_signal_check
            }
            
            if is_bank_signal_check:
                passed.append(result)
            else:
                filtered.append(result)
        
        print(f"✅ PASS (should save): {len(passed)}")
        for r in passed:
            signals = []
            if r["has_payee"]: signals.append("Payee")
            if r["has_note"]: signals.append("Note")
            if r["has_link"]: signals.append("Link")
            if r["is_debit"]: signals.append("Debit")
            if r["is_today"]: signals.append("Today")
            print(f"  ID {r['id']:3} | {r['date']} | ${r['amount']:>8} | Signals: {', '.join(signals)}")
        
        print(f"\n❌ FILTER (should skip): {len(filtered)}")
        for r in filtered:
            print(f"  ID {r['id']:3} | {r['date']} | ${r['amount']:>8} | Payee: {r['payee']} | Note: {r['note']}")
        
        print(f"\n{'='*100}")
        print(f"EXPECTED IN APP: {len(passed)} transactions")
        print(f"ACTUAL IN APP: 15 transactions")
        print(f"{'='*100}\n")
        
    finally:
        db.close()
