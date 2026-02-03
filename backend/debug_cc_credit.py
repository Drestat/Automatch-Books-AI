import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("debug-cc-credit")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
def debug_cc_credit():
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
    
    print(f"\n{'='*140}")
    print(f"DEBUGGING CREDIT CARD CREDIT QUERY")
    print(f"{'='*140}\n")
    
    # Try different query forms
    queries = [
        "SELECT * FROM CreditCardCredit",
        "SELECT * FROM CreditCardCredit MAXRESULTS 10",
        "SELECT Id, TotalAmt FROM CreditCardCredit MAXRESULTS 10"
    ]
    
    for q in queries:
        print(f"Query: {q}")
        try:
            result = client.query(q)
            print(f"✅ Success! Found {len(result.get('CreditCardCredit', []))} items.")
            if "CreditCardCredit" in result:
                items = result["CreditCardCredit"] if isinstance(result["CreditCardCredit"], list) else [result["CreditCardCredit"]]
                for item in items:
                     print(f"   ID: {item.get('Id')} | Amt: {item.get('TotalAmt')} | Ref: {item.get('DocNumber')}")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    pass
