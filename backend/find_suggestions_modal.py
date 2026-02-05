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
app = modal.App("find-suggestions-modal")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def find_suggestions():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    from app.core.feed_logic import FeedLogic
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    txs = session.query(Transaction).all()
    print(f"Analyzing {len(txs)} transactions for suggestions...")
    
    found = 0
    for tx in txs:
        is_matched, reason = FeedLogic.analyze(tx.raw_json or {})
        if "Auto-Match" in reason:
            print(f"--- SUGGESTION FOUND (ID: {tx.id}) ---")
            print(f"Reason: {reason}")
            print(json.dumps(tx.raw_json, indent=2))
            print("\n")
            found += 1
            if found >= 3: break
                
    if found == 0:
        print("No auto-match suggestions found in the current data.")

if __name__ == "__main__":
    pass
