import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def analyze_qbo_transactions():
    db = SessionLocal()
    try:
        # Get the Checking account (ID 35)
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        if not checking:
            print("❌ Checking account not found")
            return
        
        print(f"📊 Analyzing Checking Account (ID: {checking.id})")
        print(f"Realm ID: {checking.realm_id}\n")
        
        # Get QBO connection
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        if not conn:
            print("❌ No QBO connection found")
            return
        
        # Fetch LIVE data from QBO
        client = QBOClient(db, conn)
        print("🔄 Fetching LIVE data from QuickBooks...\n")
        
        # Query for Purchase transactions in Checking account
        # Note: QBO doesn't support WHERE on AccountRef directly, we need to fetch all and filter
        query = "SELECT * FROM Purchase MAXRESULTS 1000"
        result = client.query(query)
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        # Filter for Checking account
        qbo_purchases = [
            tx for tx in all_purchases 
            if tx.get("AccountRef", {}).get("value") == checking.id
        ]
        
        print(f"✅ Found {len(qbo_purchases)} Purchase transactions from QBO\n")
        print("="*80)
        
        # Analyze each transaction
        for_review = []
        categorized = []
        
        for tx in qbo_purchases:
            tx_id = tx.get("Id")
            amount = tx.get("TotalAmt")
            date = tx.get("TxnDate")
            entity_name = tx.get("EntityRef", {}).get("name", "N/A")
            
            # Check for LinkedTxn (this is the KEY indicator)
            linked_txns = tx.get("LinkedTxn", [])
            has_linked = len(linked_txns) > 0
            
            # Check for category in Line items
            has_category = False
            category_name = "N/A"
            
            if "Line" in tx:
                for line in tx["Line"]:
                    if "AccountBasedExpenseLineDetail" in line:
                        detail = line["AccountBasedExpenseLineDetail"]
                        if "AccountRef" in detail:
                            category_name = detail["AccountRef"].get("name", "N/A")
                            # Check if it's NOT uncategorized
                            if "Uncategorized" not in category_name and category_name != "N/A":
                                has_category = True
            
            # Determine status based on QBO logic
            # Key insight: LinkedTxn presence = Categorized
            # No LinkedTxn but has category = QBO suggested category (still "For Review")
            
            status_info = {
                "id": tx_id,
                "date": date,
                "amount": amount,
                "entity": entity_name,
                "has_linked_txn": has_linked,
                "linked_count": len(linked_txns),
                "has_category": has_category,
                "category_name": category_name,
                "qbo_status": "CATEGORIZED" if has_linked else "FOR_REVIEW"
            }
            
            if has_linked:
                categorized.append(status_info)
            else:
                for_review.append(status_info)
        
        # Print summary
        print(f"\n📈 SUMMARY:")
        print(f"Total Transactions: {len(qbo_purchases)}")
        print(f"For Review: {len(for_review)}")
        print(f"Categorized: {len(categorized)}\n")
        
        print("="*80)
        print("🟢 CATEGORIZED TRANSACTIONS (Has LinkedTxn):")
        print("="*80)
        for tx in categorized:
            print(f"ID: {tx['id']} | Date: {tx['date']} | Amount: ${tx['amount']}")
            print(f"  Entity: {tx['entity']}")
            print(f"  Category: {tx['category_name']}")
            print(f"  LinkedTxn Count: {tx['linked_count']}")
            print()
        
        print("="*80)
        print("🟡 FOR REVIEW TRANSACTIONS (No LinkedTxn):")
        print("="*80)
        for tx in for_review[:5]:  # Show first 5
            print(f"ID: {tx['id']} | Date: {tx['date']} | Amount: ${tx['amount']}")
            print(f"  Entity: {tx['entity']}")
            print(f"  Category: {tx['category_name']} (QBO Suggested)")
            print(f"  Has Category Field: {tx['has_category']}")
            print()
        
        if len(for_review) > 5:
            print(f"... and {len(for_review) - 5} more\n")
        
        # Now compare with our DB
        print("="*80)
        print("🔍 COMPARING WITH OUR DATABASE:")
        print("="*80)
        
        our_txs = db.query(Transaction).filter(
            Transaction.account_id == checking.id
        ).all()
        
        print(f"Our DB has {len(our_txs)} transactions for Checking\n")
        
        # Check for discrepancies
        qbo_ids = {tx.get("Id") for tx in qbo_purchases}
        our_ids = {tx.id for tx in our_txs}
        
        missing_in_db = qbo_ids - our_ids
        extra_in_db = our_ids - qbo_ids
        
        if missing_in_db:
            print(f"⚠️  Missing in our DB: {missing_in_db}")
        if extra_in_db:
            print(f"⚠️  Extra in our DB (not in QBO): {extra_in_db}")
        
        # Check matching logic
        print("\n📋 OUR MATCHING LOGIC STATUS:")
        our_matched = [tx for tx in our_txs if tx.is_qbo_matched]
        our_unmatched = [tx for tx in our_txs if not tx.is_qbo_matched]
        
        print(f"is_qbo_matched=True: {len(our_matched)}")
        print(f"is_qbo_matched=False: {len(our_unmatched)}\n")
        
        # Show the "matched" ones
        print("Our 'Matched' transactions:")
        for tx in our_matched[:5]:
            print(f"  ID: {tx.id} | ${tx.amount} | Category: {tx.suggested_category_name}")
        
    finally:
        db.close()

if __name__ == "__main__":
    analyze_qbo_transactions()
