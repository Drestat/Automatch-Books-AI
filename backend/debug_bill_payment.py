import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("debug-bill-payment")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
def debug_bill_payment():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, BankAccount
    from app.services.qbo_client import QBOClient
    import os
    import json
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
        
    client = QBOClient(session, conn)
    
    # Get active account info (Mastercard)
    accounts = session.query(BankAccount).filter_by(is_active=True).all()
    active_ids = [a.id for a in accounts]
    print(f"Active Account IDs: {active_ids}")
    for a in accounts:
        print(f"  {a.name}: {a.id}")
        
    print(f"\n{'='*140}")
    print(f"FETCHING BILL PAYMENTS FROM QBO")
    print(f"{'='*140}\n")
    
    # Select just enough to identify
    query = "SELECT * FROM BillPayment MAXRESULTS 50" 
    result = client.query(query)
    
    # Check if empty or list
    bps = []
    if "BillPayment" in result:
        bps = result["BillPayment"] if isinstance(result["BillPayment"], list) else [result["BillPayment"]]
    
    print(f"Found {len(bps)} BillPayments.")
    
    norton_found = False
    
    for bp in bps:
        # Check if relevant to Norton or date
        date = bp.get("TxnDate")
        # Look for Norton in vendor ref (EntityRef? No, VendorRef usually in 'VendorRef' or 'Payee')
        # BillPayment has 'VendorRef'
        vendor = bp.get("VendorRef", {}).get("name", "Unknown")
        amount = bp.get("TotalAmt")
        
        # Check identifying details
        is_norton = "Norton" in vendor
        is_date_match = date == "2026-01-01"
        
        if is_norton or is_date_match:
            print(f"\n🔎 Potential Match Found:")
            print(f"   ID: {bp.get('Id')}")
            print(f"   Vendor: {vendor}")
            print(f"   Date: {date}")
            print(f"   Amount: {amount}")
            print(f"   Type: {bp.get('PayType')}")
            
            # Check Account Details
            acc_id = None
            if "CheckPayment" in bp:
                print("   Subtype: CheckPayment")
                if "BankAccountRef" in bp["CheckPayment"]:
                    ref = bp["CheckPayment"]["BankAccountRef"]
                    print(f"   BankAccountRef: {ref}")
                    acc_id = ref.get("value")
            
            if "CreditCardPayment" in bp:
                print("   Subtype: CreditCardPayment")
                if "CCAccountRef" in bp["CreditCardPayment"]:
                    ref = bp["CreditCardPayment"]["CCAccountRef"]
                    print(f"   CCAccountRef: {ref}")
                    acc_id = ref.get("value")
            
            print(f"   Extracted Account ID: {acc_id}")
            if acc_id in active_ids:
                print("   ✅ MATCHES Active Account!")
            else:
                print(f"   ❌ Account ID {acc_id} NOT in Active IDs {active_ids}")
            
            print(f"   Full JSON: {json.dumps(bp)}")
            
            if is_norton: norton_found = True

    if not norton_found:
        print("\n❌ Norton Lumber BillPayment NOT found in first 50 results.")

if __name__ == "__main__":
    pass
