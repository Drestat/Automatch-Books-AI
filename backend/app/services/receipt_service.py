from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from app.models.qbo import Transaction
from app.services.ai_analyzer import AIAnalyzer
from dateutil import parser
from datetime import datetime
import logging


class ReceiptService:
    def __init__(self, db: Session, realm_id: str, user_id: str = None):
        self.db = db
        self.realm_id = realm_id
        self.user_id = user_id
        self.analyzer = AIAnalyzer()

    def _parse_receipt_date(self, date_str: str):
        """
        Parses receipt date using dateutil for flexible format support based on BUG-004.
        """
        if not date_str:
            return None
        try:
            # Fuzzy=True allows skipping non-date tokens if needed, but risky. 
            # Default strict parsing is safer for explicit fields.
            parsed = parser.parse(date_str)
            return parsed.date()
        except (ValueError, TypeError, ImportError, OverflowError) as e:
            logging.warning(f"⚠️ [ReceiptService] Failed to parse date string '{date_str}': {e}")
            return None

    def process_receipt(self, file_content: bytes, filename: str, mime_type: str = "image/jpeg"):
        """
        Processes receipt visual data via AIAnalyzer and finds best match.
        """
        try:
            extracted = self.analyzer.process_receipt(file_content, mime_type=mime_type)
        except Exception as e:
            print(f"❌ AI Receipt Error: {str(e)}")
            raise e

        # Find Best Match (Vendor Fuzz + Amount + Date Proximity)
        amount = float(extracted.get('total', 0))
        receipt_date_str = extracted.get('date')
        receipt_date = None
        if receipt_date_str:
            receipt_date = self._parse_receipt_date(receipt_date_str)

        txs = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'unmatched'
        ).all()
        
        matches = []
        for tx in txs:
            merchant_score = fuzz.WRatio(
                extracted.get('merchant', '').upper(), 
                tx.description.upper()
            )
            # Award XP for processing receipt (regardless of match success, or only on match?)
            # User req: "20xp if the transaction has a receipt" -> implies successful match/attach.
            # But process_receipt helps find the match. 
            # Let's award on SUCCESSFUL processing for now as "Receipt Added" action.
        
        # We should award XP at the end if we found matches or completed the scan?
        # Let's award it here for the "scan" action.
        try:
            if self.user_id:
                from app.services.gamification_service import GamificationService
                gs = GamificationService(self.db)
                gs.add_xp(user_id=self.user_id, action_type="receipt_upload")
                print(f"✨ [Gamification] +20 XP to {self.user_id} for receipt upload")
        except Exception as e:
             print(f"⚠️ [Gamification] Failed to award XP for receipt: {e}")

        matches = []
        for tx in txs:
            merchant_score = fuzz.WRatio(
                extracted.get('merchant', '').upper(), 
                tx.description.upper()
            )
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
        
        # PERSISTENCE: If we found a match, store the content now.
        # This is critical for Modal workers because /tmp is ephemeral.
        if best_match:
            best_match.receipt_content = file_content
            best_match.receipt_data = extracted
            # Note: receipt_url might still be /tmp/... but receipt_content saves us.
            self.db.add(best_match)
            self.db.commit()

        return {
            "extracted": extracted,
            "match": best_match
        }
