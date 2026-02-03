import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("verify-match-suggestions")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def verify_match_suggestions():
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
    print(f"THEORY: These are bank feed transactions with match suggestions")
    print(f"They have AccountRef (category suggestion) but NO LinkedTxn (not matched yet)")
    print(f"{'='*160}\n")
    
    all_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    for target_date, target_desc in target_txs:
        for tx in all_txs:
            date_str = tx.date.strftime("%m/%d/%Y") if tx.date else "N/A"
            if target_date == date_str and target_desc.lower() in (tx.description or "").lower():
                print(f"\n{'='*160}")
                print(f"{target_date} - {tx.description}")
                print(f"{'='*160}")
                print(f"Category: {tx.suggested_category_name}")
                print(f"is_bank_feed_import: {tx.is_bank_feed_import}")
                print(f"is_qbo_matched: {tx.is_qbo_matched}")
                
                # Check raw JSON for LinkedTxn
                has_linked = False
                if tx.raw_json and "Line" in tx.raw_json:
                    for line in tx.raw_json["Line"]:
                        if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                            has_linked = True
                            break
                
                print(f"Has LinkedTxn: {has_linked}")
                print(f"Has AccountRef: {tx.suggested_category_name is not None}")
                
                # Determine status
                if tx.is_bank_feed_import and not has_linked and tx.suggested_category_name:
                    print(f"\n✅ MATCHES THEORY: Bank feed with category suggestion, no LinkedTxn")
                    print(f"   → Should be in FOR REVIEW (waiting to be matched)")
                elif not tx.is_bank_feed_import:
                    print(f"\n⚠️  This is a MANUAL ENTRY (TxnType=54)")
                    print(f"   → QBO might be showing it as a match suggestion for a bank feed transaction")
                
                break
    
    print(f"\n{'='*160}")
    print(f"SUMMARY")
    print(f"{'='*160}")
    print(f"\nBank feed transactions with categories but NO LinkedTxn:")
    print(f"These have QBO's auto-match suggestions (AccountRef) but haven't been matched yet")
    print(f"They should ALL be in FOR REVIEW tab\n")
    
    bank_feed_with_cat_no_link = []
    for tx in all_txs:
        if tx.is_bank_feed_import and tx.suggested_category_name:
            # Check for LinkedTxn
            has_linked = False
            if tx.raw_json and "Line" in tx.raw_json:
                for line in tx.raw_json["Line"]:
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        has_linked = True
                        break
            
            if not has_linked:
                bank_feed_with_cat_no_link.append(tx)
    
    print(f"Total: {len(bank_feed_with_cat_no_link)}")
    for tx in bank_feed_with_cat_no_link:
        date_str = tx.date.strftime("%m/%d/%Y") if tx.date else "N/A"
        status = "FOR REVIEW" if not tx.is_qbo_matched else "CATEGORIZED (WRONG!)"
        print(f"  {date_str} - {tx.description[:40]:<40} | {tx.suggested_category_name[:30]:<30} | {status}")

if __name__ == "__main__":
    pass
