import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("find-norton")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
def find_norton():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    client = QBOClient(session, conn)
    
    print(f"\n{'='*140}")
    print(f"SEARCHING FOR NORTON LUMBER IN QBO")
    print(f"{'='*140}\n")
    
    # Try different entity types
    entity_types = ["Purchase", "Bill", "Expense"]
    
    for entity_type in entity_types:
        print(f"\nSearching {entity_type} entities...")
        try:
            query = f"SELECT * FROM {entity_type} WHERE TxnDate >= '2025-12-01' AND TxnDate <= '2026-02-01'"
            result = client.query(query)
            
            if entity_type in result:
                items = result[entity_type] if isinstance(result[entity_type], list) else [result[entity_type]]
                
                for item in items:
                    # Check if it's Norton Lumber
                    entity_ref = item.get("EntityRef", {})
                    vendor_name = entity_ref.get("name", "")
                    
                    if "Norton" in vendor_name or "Lumber" in vendor_name:
                        print(f"\n✅ FOUND in {entity_type}:")
                        print(f"   ID: {item.get('Id')}")
                        print(f"   Vendor: {vendor_name}")
                        print(f"   Date: {item.get('TxnDate')}")
                        print(f"   Amount: {item.get('TotalAmt')}")
                        print(f"   DocNumber: {item.get('DocNumber')}")
                        
                        # Check account
                        if "Line" in item:
                            for line in item["Line"]:
                                if "AccountBasedExpenseLineDetail" in line:
                                    detail = line["AccountBasedExpenseLineDetail"]
                                    if "AccountRef" in detail:
                                        account = detail["AccountRef"]
                                        print(f"   Account: {account.get('name')} (ID: {account.get('value')})")
                        
                        print(f"\n   Full JSON:")
                        import json
                        print(json.dumps(item, indent=2))
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    pass
