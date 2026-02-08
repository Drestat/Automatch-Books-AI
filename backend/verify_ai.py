from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService
import json

def verify_ai_logic():
    db = SessionLocal()
    realm_id = '9341456245321396'
    service = AnalysisService(db, realm_id)
    
    # Analyze only ID 33
    print("🧠 [Simulation] Running AI Analysis for TX 33...")
    results = service.analyze_transactions(tx_id='33')
    
    print("\n✅ AI Output for ID 33:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    verify_ai_logic()
