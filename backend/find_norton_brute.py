import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("find-norton-brute")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
def find_norton_brute():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection
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
    
    # Target: 2026-01-01, Amount ~103.55
    target_date = "2026-01-01"
    target_amount = 103.55
    
    entities = ["Check", "JournalEntry", "Transfer", "CreditCardCredit", "Payment", "Purchase", "Deposit"]
    
    print(f"\n{'='*140}")
    print(f"BRUTE FORCE SEARCH: {target_date} / ${target_amount}")
    print(f"{'='*140}\n")
    
    found_any = False
    
    for entity in entities:
        print(f"Checking {entity}...")
        try:
            # Query by date range around the target
            query = f"SELECT * FROM {entity} WHERE TxnDate = '{target_date}'"
            result = client.query(query)
            
            items = []
            if entity in result:
                items = result[entity] if isinstance(result[entity], list) else [result[entity]]
            
            for item in items:
                amt = item.get("TotalAmt")
                if amt == target_amount:
                    print(f"\n✅ FOUND MATCH in {entity}!")
                    print(f"   ID: {item.get('Id')}")
                    print(f"   Payee: {item.get('EntityRef', {}).get('name')}")
                    print(f"   DocNumber: {item.get('DocNumber')}")
                    print(f"   PrivateNote: {item.get('PrivateNote')}")
                    print(f"   JSON: {json.dumps(item)}")
                    found_any = True
        except Exception as e:
            print(f"  Error querying {entity}: {e}")
            
    if not found_any:
        print("\n❌ STILL NOT FOUND matching exact date and amount in standard entities.")

if __name__ == "__main__":
    pass
