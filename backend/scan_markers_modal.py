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
app = modal.App("scan-markers-modal")
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
    print(f"Scanning {len(all_txs)} transactions...")
    
    found = 0
    for tx in all_txs:
        raw = tx.raw_json or {}
        note = raw.get("PrivateNote", "")
        if note:
            # Print if note contains # (potential tag) or other interesting markers
            if "#" in note or "AutoMatch" in note or "Accepted" in note:
                print(f"ID: {tx.id} | Note: {note}")
                found += 1
                
    if found == 0:
        print("No markers found in any PrivateNote.")

if __name__ == "__main__":
    pass
