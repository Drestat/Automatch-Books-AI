import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-missing-txs")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_missing_txs():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # The 5 transactions from the screenshot
    target_txs = [
        ("01/13/2026", "Squeaky Kleen"),
        ("01/06/2026", "Bob's Burger"),
        ("01/06/2026", "Squeaky Kleen"),
        ("01/01/2026", "Norton Lumber"),
        ("12/26/2025", "Tania's Nursery"),
    ]
    
    print(f"\n{'='*160}")
    print(f"CHECKING FOR 5 TRANSACTIONS FROM QBO BANKING SCREENSHOT")
    print(f"{'='*160}\n")
    
    all_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"Total Mastercard transactions in DB: {len(all_txs)}\n")
    
    for target_date, target_desc in target_txs:
        print(f"\n{'='*160}")
        print(f"Looking for: {target_date} - {target_desc}")
        print(f"{'='*160}")
        
        found = False
        for tx in all_txs:
            date_str = tx.date.strftime("%m/%d/%Y") if tx.date else "N/A"
            if target_date == date_str and target_desc.lower() in (tx.description or "").lower():
                found = True
                print(f"✅ FOUND in database:")
                print(f"   Description: {tx.description}")
                print(f"   Category: {tx.suggested_category_name}")
                print(f"   is_qbo_matched: {tx.is_qbo_matched}")
                print(f"   is_excluded: {tx.is_excluded}")
                print(f"   is_bank_feed_import: {tx.is_bank_feed_import}")
                
                # Determine which tab it should be in
                if tx.is_excluded:
                    tab = "EXCLUDED"
                elif tx.is_qbo_matched:
                    tab = "CATEGORIZED"
                else:
                    tab = "FOR REVIEW"
                
                print(f"   Current tab: {tab}")
                break
        
        if not found:
            print(f"❌ NOT FOUND in database!")
    
    print(f"\n{'='*160}")
    print(f"FOR REVIEW TAB SHOULD CONTAIN:")
    print(f"{'='*160}\n")
    
    for_review = [tx for tx in all_txs if not tx.is_excluded and not tx.is_qbo_matched]
    print(f"Total in For Review: {len(for_review)}\n")
    
    for tx in for_review:
        date_str = tx.date.strftime("%m/%d/%Y") if tx.date else "N/A"
        print(f"{date_str} - {tx.description}")

if __name__ == "__main__":
    pass
