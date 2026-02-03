import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("dump-date-txs")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
def dump_date_txs():
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
    target_date = "2026-01-01"
    
    entities = ["Purchase", "JournalEntry", "Transfer", "CreditCardCredit", "Payment", "BillPayment", "Check", "Result"] # Result is sometimes used for generic
    
    print(f"\n{'='*140}")
    print(f"DUMPING ALL TRANSACTIONS FOR {target_date}")
    print(f"{'='*140}\n")
    
    for entity in entities:
        try:
            query = f"SELECT * FROM {entity} WHERE TxnDate = '{target_date}'"
            result = client.query(query)
            
            items = []
            if entity in result:
                items = result[entity] if isinstance(result[entity], list) else [result[entity]]
            
            if items:
                print(f"\n--- {entity} ({len(items)}) ---")
                for item in items:
                    print(f"ID: {item.get('Id')} | Amt: {item.get('TotalAmt')} | Ref: {item.get('DocNumber')}")
                    entity_ref = item.get('EntityRef', {}) or item.get('VendorRef', {}) or item.get('CustomerRef', {})
                    print(f"Name: {entity_ref.get('name')} (Type: {entity_ref.get('type')})")
                    print(f"Note: {item.get('PrivateNote')}")
                    
        except Exception as e:
            # Ignore errors for entities that might not support date filtering or other API quirks
            pass

if __name__ == "__main__":
    pass
