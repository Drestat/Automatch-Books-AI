import modal
import os
from dotenv import dotenv_values
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("verify-elegant-logic")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def verify_logic():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Key Entities to Check
    targets = [
        {"name": "Lara's Lamination", "expected": True, "type": "Manual (Fresh)"},
        {"name": "Tania's Nursery", "expected": False, "type": "Manual (Modified)"},
        {"name": "Norton Lumber", "expected": True, "type": "Bill Payment (Linked)"},
        {"name": "Bob's Burger", "expected": False, "type": "Bank Feed (Unlinked)"},
        {"name": "Squeaky Kleen", "expected": False, "type": "Bank Feed (Unlinked)"},
    ]
    
    print(f"\nExample Verification Results:")
    print(f"{'='*100}")
    print(f"{'Entity':<25} | {'Type':<20} | {'Status':<15} | {'Expected':<15} | {'Result'}")
    print(f"{'-'*100}")
    
    passed_count = 0
    
    for target in targets:
        # Simple LIKE query
        tx = session.query(Transaction).filter(Transaction.description.ilike(f"%{target['name']}%")).first()
        
        if tx:
            status = "CATEGORIZED" if tx.is_qbo_matched else "FOR REVIEW"
            expected_str = "CATEGORIZED" if target['expected'] else "FOR REVIEW"
            match = tx.is_qbo_matched == target['expected']
            badge = "✅ PASS" if match else "❌ FAIL"
            if match: passed_count += 1
            
            print(f"{target['name']:<25} | {target['type']:<20} | {status:<15} | {expected_str:<15} | {badge}")
        else:
            print(f"{target['name']:<25} | {target['type']:<20} | {'NOT FOUND':<15} | {'--':<15} | ⚠️ MISSING")

    print(f"{'-'*100}")
    
    # Overall Counters
    total = session.query(Transaction).count()
    for_review = session.query(Transaction).filter(Transaction.is_qbo_matched == False).count()
    categorized = session.query(Transaction).filter(Transaction.is_qbo_matched == True).count()
    
    print(f"\nTotal Transactions: {total}")
    print(f"For Review: {for_review}")
    print(f"Categorized: {categorized}")

if __name__ == "__main__":
    pass
