import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("verify-screenshot-matches")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def verify_screenshot_matches():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # The 5 transactions from the screenshot that should be "For Review"
    screenshot_txns = [
        ("Bob's Burger", "01/06/2026"),
        ("Norton Lumber", "01/01/2026"),
        ("Squeaky Kleen", "01/06/2026"),
        ("Squeaky Kleen", "01/13/2026"),
        ("Tania's Nursery", "12/26/2025")
    ]
    
    print(f"\n{'='*120}")
    print(f"VERIFICATION: Screenshot 'For Review' Transactions")
    print(f"{'='*120}\n")
    print(f"{'Description':<25} | {'Date':<12} | {'Amount':<10} | {'DB Status':<15} | {'Match?'}")
    print(f"{'-'*120}")
    
    all_match = True
    
    for desc, date_str in screenshot_txns:
        # Find transaction
        tx = session.query(Transaction).filter(
            Transaction.description.ilike(f"%{desc}%")
        ).order_by(Transaction.date.desc()).first()
        
        if tx:
            db_status = "FOR REVIEW" if not tx.is_qbo_matched else "CATEGORIZED"
            expected = "FOR REVIEW"
            match = db_status == expected
            badge = "✅" if match else "❌"
            
            if not match:
                all_match = False
            
            print(f"{desc:<25} | {date_str:<12} | ${tx.amount:<9} | {db_status:<15} | {badge}")
        else:
            print(f"{desc:<25} | {date_str:<12} | {'N/A':<10} | {'NOT FOUND':<15} | ⚠️")
            all_match = False
    
    print(f"{'-'*120}\n")
    
    if all_match:
        print("✅ SUCCESS: All screenshot transactions correctly marked as 'For Review'")
    else:
        print("❌ MISMATCH: Some transactions don't match expected status")
    
    # Show overall stats
    total_for_review = session.query(Transaction).filter(Transaction.is_qbo_matched == False).count()
    print(f"\nTotal 'For Review' in DB: {total_for_review}")

if __name__ == "__main__":
    pass
