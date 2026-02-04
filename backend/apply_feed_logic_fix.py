
import sys
import os
from sqlalchemy.orm import Session
import time

# Add the backend directory to sys.path to import app modules
sys.path.append('/Users/andresmunoz2026/Library/Mobile Documents/com~apple~CloudDocs/2026 Projects/Antigravity/Quickbooks Bank Transactions 2/backend')

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.core.feed_logic import FeedLogic

def apply_feed_logic_fix():
    print("🚀 Starting Database Remediation...")
    db = SessionLocal()
    
    try:
        # Get all transactions
        txs = db.query(Transaction).all()
        print(f"📊 Found {len(txs)} transactions to analyze.")
        
        updated_count = 0
        
        for tx in txs:
            if not tx.raw_json:
                continue
                
            # Re-run logic
            new_is_matched, reasons = FeedLogic.analyze(tx.raw_json)
            
            # Compare and Update
            if tx.is_qbo_matched != new_is_matched:
                print(f"🔄 Updating {tx.id} ({tx.description}): {tx.is_qbo_matched} -> {new_is_matched} (Reason: {reasons})")
                tx.is_qbo_matched = new_is_matched
                updated_count += 1
                
        db.commit()
        print(f"✅ Remediation Complete. Updated {updated_count} transactions.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    apply_feed_logic_fix()
