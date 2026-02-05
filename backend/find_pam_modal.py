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
app = modal.App("find-pam-modal")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def find_pam():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    txs = session.query(Transaction).filter(Transaction.description.contains("Pam")).all()
    print(f"Found {len(txs)} transactions matching 'Pam':")
    
    for tx in txs:
        print(f"ID: {tx.id} | Description: {tx.description} | Matched: {tx.is_qbo_matched}")
        print(json.dumps(tx.raw_json, indent=2))
        print("\n")

if __name__ == "__main__":
    pass
