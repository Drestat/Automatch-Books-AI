from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from app.models.qbo import Transaction
from app.services.ai_analyzer import AIAnalyzer

class ReceiptService:
    def __init__(self, db: Session, realm_id: str):
        self.db = db
        self.realm_id = realm_id
        self.analyzer = AIAnalyzer()

    def process_receipt(self, file_content: bytes, filename: str):
        """
        Processes receipt visual data via AIAnalyzer and finds best match.
        """
        try:
            extracted = self.analyzer.process_receipt(file_content)
        except Exception as e:
            print(f"❌ AI Receipt Error: {str(e)}")
            raise e

        # Find Best Match
        amount = float(extracted.get('total', 0))
        txs = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'unmatched'
        ).all()
        
        best_match = None
        for tx in txs:
            merchant_score = fuzz.WRatio(extracted.get('merchant', ''), tx.description)
            # Ensure safe float conversion and absolute value comparison
            amount_diff = abs(abs(float(tx.amount)) - amount)
            
            if merchant_score > 70 and amount_diff < (amount * 0.1):
                best_match = tx
                break
        
        return {
            "extracted": extracted,
            "match": best_match
        }
