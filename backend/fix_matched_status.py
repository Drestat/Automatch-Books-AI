import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, Base
from app.models.qbo import Transaction, QBOConnection, BankAccount
from app.services.transaction_service import TransactionService

def fix_matched_status():
    db = SessionLocal()
    try:
        # Get all relevant connections
        connections = db.query(QBOConnection).all()
        print(f"🔍 Found {len(connections)} QBO connections.")

        for conn in connections:
            print(f"🔄 Processing realm: {conn.realm_id}")
            service = TransactionService(db, conn)
            
            # Fetch active account IDs for this realm
            active_banks = db.query(BankAccount).filter(
                BankAccount.realm_id == conn.realm_id,
                BankAccount.is_active == True
            ).all()
            
            if not active_banks:
                print(f"⚠️ No active accounts for realm {conn.realm_id}. Skipping.")
                continue
                
            active_account_ids = [str(b.id) for b in active_banks]
            
            # Get existing transactions for this realm
            transactions = db.query(Transaction).filter(
                Transaction.realm_id == conn.realm_id,
                Transaction.account_id.in_(active_account_ids)
            ).all()
            
            print(f"📊 Found {len(transactions)} existing transactions in DB for active accounts.")
            
            updated_count = 0
            for tx in transactions:
                # We need the original QBO JSON to re-run the categorization detection
                p = tx.raw_json
                if not p:
                    continue
                
                # Re-run categorization detection from TransactionService (simplified)
                qbo_category_name = None
                
                has_linked_txn = False
                if "Line" in p:
                    for line in p["Line"]:
                        # 1. Check for Linked Transactions
                        if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                            has_linked_txn = True

                        detail = None
                        if "AccountBasedExpenseLineDetail" in line:
                            detail = line["AccountBasedExpenseLineDetail"]
                        elif "JournalEntryLineDetail" in line:
                            detail = line["JournalEntryLineDetail"]
                        elif "DepositLineDetail" in line:
                            detail = line["DepositLineDetail"]
                        elif "SalesItemLineDetail" in line:
                            detail = line["SalesItemLineDetail"]
                        elif "ItemBasedExpenseLineDetail" in line:
                            detail = line["ItemBasedExpenseLineDetail"]
                        
                        if detail:
                            if "AccountRef" in detail:
                                ref_name = detail["AccountRef"].get("name")
                                ref_id = str(detail["AccountRef"].get("value"))
                                
                                # Use string comparison for acc_id (tx.account_id is already in DB)
                                if ref_name and "Uncategorized" not in ref_name and ref_id != str(tx.account_id):
                                    qbo_category_name = ref_name
                                    break
                            elif "ItemRef" in detail:
                                # For Item-based transactions, the "category" is the item itself
                                qbo_category_name = detail["ItemRef"].get("name")
                                break
                
                if (qbo_category_name or has_linked_txn) and not tx.is_qbo_matched:
                    print(f"✅ Marking tx {tx.id} as matched (Category: {qbo_category_name or 'Linked Entry'})")
                    tx.is_qbo_matched = True
                    updated_count += 1
            
            db.commit()
            print(f"🎉 Updated {updated_count} transactions for realm {conn.realm_id}.")

    finally:
        db.close()

if __name__ == "__main__":
    fix_matched_status()
