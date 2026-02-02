
import sys
import os
import json
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection, BankAccount

def determine_status_strict(tx):
    raw_json = tx.raw_json
    if not raw_json:
        return False, None

    has_linked_txn = False
    qbo_category_name = None
    
    if "Line" in raw_json:
        for line in raw_json["Line"]:
            if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                has_linked_txn = True
            
            # Check line details for category
            detail = None
            if "AccountBasedExpenseLineDetail" in line:
                detail = line["AccountBasedExpenseLineDetail"]
            elif "ItemBasedExpenseLineDetail" in line:
                detail = line["ItemBasedExpenseLineDetail"]
            elif "JournalEntryLineDetail" in line:
                detail = line["JournalEntryLineDetail"]
            elif "DepositLineDetail" in line:
                detail = line["DepositLineDetail"]
            
            if detail:
                    if "AccountRef" in detail:
                        ref_name = detail["AccountRef"].get("name")
                        ref_val = detail["AccountRef"].get("value")
                        if ref_name and "Uncategorized" not in ref_name and str(ref_val) != str(tx.account_id):
                                qbo_category_name = ref_name
                    elif "ItemRef" in detail:
                        # For Items, we treat it as categorized
                        qbo_category_name = detail["ItemRef"].get("name")
    
    desc_upper = (tx.description or "").upper()
    is_weak_desc = "UNCATEGORIZED" in desc_upper or "OPENING BALANCE" in desc_upper
    
    # STRICT MATCH LOGIC: LINKED ONLY
    is_matched = False
    if has_linked_txn and not is_weak_desc:
        is_matched = True
        if not qbo_category_name:
            qbo_category_name = "Matched to QBO Entry"
    
    # If explicitly approved in our app, keep it matched
    if tx.status == 'approved':
        is_matched = True

    return is_matched, qbo_category_name

def fix_transactions():
    db = SessionLocal()
    try:
        connections = db.query(QBOConnection).all()
        print(f"🔍 Found {len(connections)} QBO connections.")
        
        for conn in connections:
            print(f"🔄 Processing realm: {conn.realm_id}")
            
            # Get valid active account IDs
            account_objs = db.query(BankAccount).filter(
                BankAccount.realm_id == conn.realm_id,
                BankAccount.is_active == True,
                BankAccount.is_connected == True
            ).all()
            active_account_ids = [acc.id for acc in account_objs]
            print(f"   Active Accounts: {active_account_ids}")
            
            transactions = db.query(Transaction).filter(
                Transaction.realm_id == conn.realm_id
            ).all()
            
            # Filter in python to avoid issues if list is empty
            if active_account_ids:
                 transactions = [t for t in transactions if t.account_id in active_account_ids]

            print(f"📊 Found {len(transactions)} existing transactions in DB for active accounts.")
            
            updated_count = 0
            for tx in transactions:
                old_matched = tx.is_qbo_matched
                new_matched, qbo_cat = determine_status_strict(tx)
                
                changed = False
                if old_matched != new_matched:
                    tx.is_qbo_matched = new_matched
                    changed = True
                    print(f"   -> ID: {tx.id} | Matched: {old_matched} -> {new_matched} (Strict)")
                
                # If downgrading to !matched, ensure suggested_category is set
                if not new_matched and qbo_cat:
                    # Only calculate if we need to suggest it
                    # (Don't overwrite existing suggestion if user was working on it? 
                    # Actually, if we are fixing statuses, we should probably reset suggestion to the QBO truth)
                    if tx.suggested_category_name != qbo_cat:
                        tx.suggested_category_name = qbo_cat
                        changed = True
                        print(f"      Set Suggestion: {qbo_cat}")

                if changed:
                    db.add(tx)
                    updated_count += 1
            
            db.commit()
            print(f"🎉 Updated {updated_count} transactions for realm {conn.realm_id}.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_transactions()
