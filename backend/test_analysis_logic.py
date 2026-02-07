import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService
from app.models.qbo import Transaction, QBOConnection

def test_analysis():
    db = SessionLocal()
    try:
        # Get a Realm ID
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
        
        realm_id = conn.realm_id
        print(f"Using Realm: {realm_id}")

        # Find a transaction to analyze
        # Prefer one that has a description (so history match _could_ happen)
        tx = db.query(Transaction).filter(
            Transaction.realm_id == realm_id,
            Transaction.description.isnot(None)
        ).first()

        if not tx:
            print("No transactions found")
            return

        print(f"Testing Analysis on TX: {tx.id} | Desc: {tx.description}")
        print(f"Current Reasoning: {tx.reasoning}")

        service = AnalysisService(db, realm_id)
        
        # Call analyze with tx_id to force AI
        print("--- RUNNING ANALYSIS ---")
        results = service.analyze_transactions(tx_id=tx.id)
        
        print(f"Results: {results}")
        
        # Re-fetch to check updates
        db.refresh(tx)
        print(f"New Reasoning: {tx.reasoning}")
        print(f"New Category: {tx.suggested_category_name}")
        print(f"Confidence: {tx.confidence}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_analysis()
