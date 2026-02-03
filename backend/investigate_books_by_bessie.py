import sys
sys.path.insert(0, '/Users/andresmunoz2026/Library/Mobile Documents/com~apple~CloudDocs/2026 Projects/Antigravity/Quickbooks Bank Transactions 2/backend')

from app.db.session import SessionLocal
from app.models.transaction import Transaction

db = SessionLocal()
try:
    # Find the Books By Bessie transaction
    tx = db.query(Transaction).filter(
        Transaction.description.ilike('%Books By Bessie%')
    ).first()
    
    if tx:
        print(f'Transaction Found:')
        print(f'  ID: {tx.id}')
        print(f'  Description: {tx.description}')
        print(f'  Amount: ${tx.amount}')
        print(f'  Date: {tx.date}')
        print(f'  Category: {tx.category_name}')
        print(f'  is_qbo_matched: {tx.is_qbo_matched}')
        print(f'  is_excluded: {tx.is_excluded}')
        print(f'  Status: {tx.status}')
        print(f'  LinkedTxn: {tx.linked_txn}')
        print(f'  DocNumber: {tx.doc_number}')
        print(f'  SyncToken: {tx.sync_token}')
        print(f'  TxnType: {tx.txn_type}')
        print()
        print('Analysis:')
        print(f'  - In QBO: Shows as "Added" with category "Sales of Product Income"')
        print(f'  - In App: Shows in "For Review" tab (is_qbo_matched={tx.is_qbo_matched})')
        print()
        
        # Check the logic
        if tx.is_qbo_matched:
            print('  ✅ Should be in CATEGORIZED tab')
        else:
            print('  ❌ Currently in FOR REVIEW tab')
            print()
            print('  Possible reasons:')
            print(f'    1. LinkedTxn is empty/None: {tx.linked_txn is None or tx.linked_txn == "[]"}')
            print(f'    2. Status is not set correctly: {tx.status}')
            print(f'    3. Sync logic not detecting QBO categorization')
    else:
        print('Transaction not found')
finally:
    db.close()
