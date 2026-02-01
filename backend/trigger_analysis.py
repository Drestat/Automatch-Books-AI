from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService

db = SessionLocal()
realm_id = "9341456245321396" # From previous context
service = AnalysisService(db, realm_id)
print("Starting analysis...")
results = service.analyze_transactions(limit=5)
print("Analysis result:", results)
db.close()
