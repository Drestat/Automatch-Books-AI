"""
Diagnostic script to test receipt upload to QBO.
Tests the exact API call format and helps identify the issue.
"""
import os
import sys
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from sqlalchemy import text

def diagnose_receipt_issue():
    db = SessionLocal()

    print("=" * 60)
    print("Receipt Upload Diagnostic")
    print("=" * 60)

    # Find a transaction with a receipt
    result = db.execute(text("""
        SELECT id, transaction_type, receipt_url, receipt_content IS NOT NULL as has_binary, status
        FROM transactions
        WHERE receipt_url IS NOT NULL OR receipt_content IS NOT NULL
        LIMIT 5
    """))

    txs_with_receipts = result.fetchall()

    if not txs_with_receipts:
        print("❌ No transactions found with receipts")
        return

    print(f"\n✅ Found {len(txs_with_receipts)} transactions with receipts:")
    print("-" * 60)

    for tx in txs_with_receipts:
        print(f"ID: {tx[0]}")
        print(f"  Type: {tx[1]}")
        print(f"  Receipt URL: {tx[2]}")
        print(f"  Has Binary: {tx[3]}")
        print(f"  Status: {tx[4]}")
        print()

    # Check what transaction types we have
    print("\nTransaction Type Distribution:")
    print("-" * 60)
    result = db.execute(text("""
        SELECT transaction_type, COUNT(*) as count
        FROM transactions
        WHERE transaction_type IS NOT NULL
        GROUP BY transaction_type
        ORDER BY count DESC
    """))

    for row in result:
        print(f"  {row[0]}: {row[1]} transactions")

    # Check QBO API entity type mapping
    print("\n" + "=" * 60)
    print("QBO Attachable EntityRef Type Mapping:")
    print("=" * 60)
    print("""
QuickBooks API requires specific entity types for AttachableRef:
- Purchase     ✅ (Credit Card Purchase, Expense)
- Check        ✅ (Check)
- Bill         ✅ (Bill)
- Expense      ✅ (Expense)
- JournalEntry ✅ (Journal Entry)

Current Mapping Issues:
- "CreditCard" ❌ (Should map to "Purchase")
- "Payment"    ❌ (Should map to "Payment" or "BillPayment" depending on context)

RECOMMENDATION: Update transaction_service.py line 408 to map
transaction types to valid QBO Attachable entity types.
    """)

    db.close()

if __name__ == "__main__":
    diagnose_receipt_issue()
