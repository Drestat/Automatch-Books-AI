import sys
import os
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService
from app.models.qbo import Transaction

def debug_analysis():
    db = SessionLocal()
    # Replace with the user's realm_id from context or logs? 
    # I'll use a placeholder or try to find one from DB.
    # But for now, let's just inspect the AnalysisService logic dry.
    # Actually I need a real transaction to run AI against.
    
    # Let's find a transaction that corresponds to "Squeaky Kleen Car Wash"
    tx = db.query(Transaction).filter(Transaction.description.ilike('%Squeaky Kleen%')).first()
    
    if not tx:
        print("❌ Could not find Squeaky Kleen transaction locally to test.")
        # Try to find ANY transaction
        tx = db.query(Transaction).first()
        if not tx:
            print("❌ No transactions in local DB.")
            return

    print(f"✅ Found transaction: {tx.description} (ID: {tx.id})")
    print(f"   Current Reasoning: {tx.reasoning}")
    
    service = AnalysisService(db, tx.realm_id)
    
    # Mimic the re-analyze flow
    print("\n🚀 Starting Analysis...")
    try:
        # We'll use analyze_transactions with a limit of 1 and this specific ID
        # But analyze_transactions filters by 'status=unmatched'. 
        # So we must temporarily set it to unmatched?
        # Or just allow it.
        
        # Let's verify what keys the AIAnalyzer returns first.
        context = service.get_ai_context()
        print(f"   Context keys: {context.keys()}")
        
        # Call analyzer directly to see raw output
        ai_context = {
            "category_list": context['categories'],
            "history_str": "Mock History"
        }
        
        print("   Calling AIAnalyzer.analyze_batch...")
        analyses = service.analyzer.analyze_batch([tx], ai_context)
        
        if not analyses:
            print("❌ AI returned no analyses.")
            return

        analysis = analyses[0]
        print(f"\n📦 Raw AI Payload Keys: {list(analysis.keys())}")
        print(f"   Category: {analysis.get('category')}")
        print(f"   Reasoning: {analysis.get('reasoning')}")
        print(f"   Tax Note: {analysis.get('tax_deduction_note')}")
        
    except Exception as e:
        print(f"❌ Error during local debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_analysis()
