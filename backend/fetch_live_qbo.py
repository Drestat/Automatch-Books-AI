import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("fetch-live-qbo")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
})

@app.function(image=image, secrets=[secrets])
def fetch_live_data():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, BankAccount
    from app.services.qbo_client import QBOClient
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Get Mastercard account
    mastercard = session.query(BankAccount).filter(
        BankAccount.realm_id == conn.realm_id,
        BankAccount.name.ilike("%mastercard%")
    ).first()
    
    if not mastercard:
        print("No Mastercard account found")
        return
    
    print(f"\n{'='*140}")
    print(f"FETCHING LIVE DATA FROM QBO API")
    print(f"{'='*140}\n")
    print(f"Account: {mastercard.name} (ID: {mastercard.id})")
    
    # Initialize QBO Client
    client = QBOClient(session, conn)
    
    # Fetch Purchase transactions for Mastercard
    query = f"SELECT * FROM Purchase WHERE AccountRef = '{mastercard.id}'"
    print(f"\nQuery: {query}\n")
    
    try:
        purchases = client.query(query)
        print(f"✅ Found {len(purchases)} transactions in QBO API\n")
        
        print(f"{'ID':<15} | {'Date':<12} | {'Description':<35} | {'Amount':<10} | {'Has LinkedTxn'}")
        print(f"{'-'*140}")
        
        for p in purchases:
            txn_id = p.get("Id", "N/A")
            date = p.get("TxnDate", "N/A")
            
            # Get description
            entity_ref = p.get("EntityRef", {})
            vendor = entity_ref.get("name", "")
            memo = p.get("PrivateNote", "")
            desc = f"{vendor} {memo}".strip()[:35]
            
            amount = p.get("TotalAmt", 0)
            
            # Check for LinkedTxn
            has_link = False
            if "Line" in p:
                for line in p["Line"]:
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        has_link = True
                        break
            
            marker = "✅ YES" if has_link else "❌ NO"
            print(f"{txn_id:<15} | {date:<12} | {desc:<35} | ${amount:<9.2f} | {marker}")
        
        print(f"\n{'='*140}")
        print(f"SUMMARY")
        print(f"{'='*140}")
        print(f"Live QBO API: {len(purchases)} transactions")
        print(f"Our Database: 16 transactions")
        print(f"Discrepancy: {16 - len(purchases)} extra transactions in our DB")
        
        if len(purchases) < 16:
            print(f"\n⚠️  Our database has {16 - len(purchases)} stale/deleted transactions!")
            print(f"These were likely deleted or moved in QBO but our sync didn't prune them.")
        
    except Exception as e:
        print(f"❌ Error fetching from QBO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pass
