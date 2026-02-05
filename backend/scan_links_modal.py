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
app = modal.App("scan-links-modal")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def scan():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    all_txs = session.query(Transaction).all()
    print(f"Scanning {len(all_txs)} transactions for links...")
    
    found = 0
    for tx in all_txs:
        raw = tx.raw_json or {}
        # Check LinkedTxn at top level or in lines
        links = raw.get("LinkedTxn", [])
        for line in raw.get("Line", []):
            links.extend(line.get("LinkedTxn", []))
            
        if links:
            print(f"ID: {tx.id} | Links: {json.dumps(links)}")
            found += 1
                
    if found == 0:
        print("No LinkedTxn found in any transaction.")

if __name__ == "__main__":
    pass
