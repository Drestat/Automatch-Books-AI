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
app = modal.App("dump-raw-tx-modal")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def dump_raw():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get one matched and one unmatched
    matched = session.query(Transaction).filter(Transaction.is_qbo_matched == True).first()
    unmatched = session.query(Transaction).filter(Transaction.is_qbo_matched == False).first()
    
    if matched:
        print(f"--- MATCHED (ID: {matched.id}) ---")
        print(json.dumps(matched.raw_json, indent=2))
        print("\n")
        
    if unmatched:
        print(f"--- UNMATCHED (ID: {unmatched.id}) ---")
        print(json.dumps(unmatched.raw_json, indent=2))
        print("\n")

if __name__ == "__main__":
    pass
