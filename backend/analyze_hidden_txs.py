import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("analyze-hidden-txs")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def analyze_hidden():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    import json
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Get all Mastercard transactions
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"\n{'='*160}")
    print(f"ANALYZING WHY TRANSACTIONS ARE HIDDEN FROM QBO BANKING UI")
    print(f"{'='*160}\n")
    print(f"Total in DB: 16")
    print(f"Visible in QBO Banking: ~5-7")
    print(f"Hidden: ~9-11\n")
    
    print(f"Checking raw_json for clues...\n")
    print(f"{'Date':<12} | {'Description':<30} | {'LinkedTxn':<10} | {'TxnType':<10} | {'DocNumber':<12} | {'PaymentType':<15}")
    print(f"{'-'*160}")
    
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:30]
        
        # Check raw JSON
        has_link = "NO"
        txn_type = "N/A"
        doc_number = "N/A"
        payment_type = "N/A"
        
        if tx.raw_json:
            # LinkedTxn
            if "Line" in tx.raw_json:
                for line in tx.raw_json["Line"]:
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        has_link = "YES"
                        break
            
            # TxnType from PurchaseEx
            purchase_ex = tx.raw_json.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value", "N/A")
                        break
            
            # DocNumber
            doc_number = tx.raw_json.get("DocNumber", "N/A")
            
            # PaymentType
            payment_type = tx.raw_json.get("PaymentType", "N/A")
        
        print(f"{date_str:<12} | {desc:<30} | {has_link:<10} | {txn_type:<10} | {doc_number:<12} | {payment_type:<15}")
    
    print(f"\n{'='*160}")
    print(f"HYPOTHESIS: Transactions Hidden from Banking UI")
    print(f"{'='*160}")
    print(f"QBO Banking Feed typically hides transactions that:")
    print(f"1. Have LinkedTxn (already matched/added to books)")
    print(f"2. Have TxnType = '54' (manual entry, not from bank feed)")
    print(f"3. Have DocNumber (manual check/payment)")
    print(f"4. Were created manually vs imported from bank")
    print(f"\nBased on the data above, the 'hidden' transactions likely have one of these markers.")

if __name__ == "__main__":
    pass
