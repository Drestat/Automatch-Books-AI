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

        # Find Best Match (Vendor Fuzz + Amount + Date Proximity)
        amount = float(extracted.get('total', 0))
        receipt_date_str = extracted.get('date')
        receipt_date = None
        if receipt_date_str:
            try:
                from datetime import datetime
                receipt_date = datetime.strptime(receipt_date_str, "%Y-%m-%d").date()
            except:
                pass

        txs = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'unmatched'
        ).all()
        
        matches = []
        for tx in txs:
            merchant_score = fuzz.WRatio(extracted.get('merchant', ''), tx.description)
            amount_diff = abs(abs(float(tx.amount)) - amount)
            
            # Date score (100 if same day, degrades over 7 days)
            date_score = 100
            if receipt_date and tx.date:
                days_diff = abs((tx.date.date() - receipt_date).days)
                date_score = max(0, 100 - (days_diff * 15))

            # Composite Score
            # Weight: Merchant (50%), Amount (30%), Date (20%)
            is_amount_match = amount_diff < (amount * 0.05) or amount_diff < 1.0 # Within 5% or $1
            
            if merchant_score > 70 and is_amount_match:
                composite_score = (merchant_score * 0.5) + (date_score * 0.5)
                matches.append((tx, composite_score))
        
        # Sort by composite score
        matches.sort(key=lambda x: x[1], reverse=True)
        best_match = matches[0][0] if matches else None
        
        return {
            "extracted": extracted,
            "match": best_match
        }
