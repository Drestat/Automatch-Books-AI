from sqlalchemy.orm import Session
from rapidfuzz import process, fuzz
from app.models.qbo import Transaction, Category, Customer, TransactionSplit, SyncLog, QBOConnection
from app.services.ai_analyzer import AIAnalyzer
import json

class AnalysisService:
    def __init__(self, db: Session, realm_id: str):
        self.db = db
        self.realm_id = realm_id
        self.analyzer = AIAnalyzer()

    def _log(self, operation: str, entity_type: str, count: int, status: str, details: dict = None):
        log = SyncLog(
            realm_id=self.realm_id,
            operation=operation,
            entity_type=entity_type,
            count=count,
            status=status,
            details=details
        )
        self.db.add(log)
        self.db.commit()

    def get_ai_context(self):
        """Fetches categories and customers for AI context"""
        categories = self.db.query(Category).filter(Category.realm_id == self.realm_id).all()
        customers = self.db.query(Customer).filter(Customer.realm_id == self.realm_id).all()
        
        # Vendor history context
        history = self.db.query(
            Transaction.description, 
            Transaction.suggested_category_name
        ).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'approved'
        ).all()
        
        vendor_mapping = {}
        for desc, cat in history:
            if desc not in vendor_mapping:
                vendor_mapping[desc] = cat

        return {
            "categories": [c.name for c in categories],
            "customers": [c.display_name for c in customers],
            "vendor_mapping": vendor_mapping,
            "category_objs": {c.name: c for c in categories}
        }

    def analyze_transactions(self, limit: int = 100, tx_id: str = None):
        """
        Orchestrates hybrid intelligence with Rule-based logic and Gemini.
        """
        print(f"🔍 [AnalysisService] Starting analysis for realm {self.realm_id}...")
        query = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'unmatched'
        )

        if tx_id:
            query = query.filter(Transaction.id == tx_id)
        
        unmatched = query.order_by(Transaction.date.desc()).limit(limit).all()
        
        if not unmatched:
            return {"message": "No unmatched transactions found"}

        context = self.get_ai_context()
        categories_obj = context['category_objs']
        category_list = context['categories']
        vendor_mapping = context['vendor_mapping']
        
        to_analyze_with_ai = []
        results = []

        # --- Rule 1: Deterministic matching from History ---
        for tx in unmatched:
            if tx.description in vendor_mapping:
                suggested_cat = vendor_mapping[tx.description]
                print(f"✅ [Deterministic] Matched '{tx.description}' to '{suggested_cat}'")
                self._apply_suggestion(tx, suggested_cat, "Deterministic match from history.", 1.0, "history", list(categories_obj.values()))
                results.append({"id": tx.id, "analysis": {"category": suggested_cat, "method": "history"}})
            else:
                to_analyze_with_ai.append(tx)

        if not to_analyze_with_ai:
            self.db.commit()
            return results

        # --- Rule 2: AI Guess (Gemini) ---
        history_str = "\n".join([f"HISTORIC: '{desc}' -> Category: {cat}" for desc, cat in list(vendor_mapping.items())[:20]])
        ai_context = {"category_list": category_list, "history_str": history_str}

        from app.services.token_service import TokenService
        token_service = TokenService(self.db)
        
        user_id = self.db.query(QBOConnection).filter(QBOConnection.realm_id == self.realm_id).first().user_id
        cost = len(to_analyze_with_ai)
        
        if not token_service.has_sufficient_tokens(user_id, cost):
            available = token_service.get_balance(user_id)
            to_analyze_with_ai = to_analyze_with_ai[:available]
            cost = available
            if cost == 0: return results

        try:
            token_service.deduct_tokens(user_id, cost, reason=f"AI Analysis")
            analyses = self.analyzer.analyze_batch(to_analyze_with_ai, ai_context)
            
            analysis_map = {str(a.get('id')): a for a in analyses if a.get('id')}

            for tx in to_analyze_with_ai:
                analysis = analysis_map.get(str(tx.id))
                if analysis:
                    self._apply_ai_suggestion(tx, analysis, categories_obj, category_list)
                    results.append({"id": tx.id, "analysis": {**analysis, "method": "ai"}})
                    
                    # --- Rule 3: Auto-Approve High Confidence (Founder/Empire Tier) ---
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if tx.confidence and tx.confidence >= 0.95 and user.subscription_tier in ['founder', 'empire']:
                        print(f"🚀 [Auto-Approve] High confidence ({tx.confidence}) for {tx.id} (Tier: {user.subscription_tier})")
                        # Mark as pending_approval for immediate UI feedback
                        # We could call approve_transaction here, but it's better to let a separate 
                        # celery/modal task handle the QBO write to keep analysis fast.
                        # For now, we mark as pending_approval and the 'Daily Triage' ritual 
                        # will show them as ready for one-tap or bulk-approval.
                        tx.status = 'pending_approval'
                    elif tx.confidence and tx.confidence >= 0.8:
                        tx.status = 'pending_approval'
                
            self.db.commit()
            return results
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            return results

    def _apply_suggestion(self, tx, suggested_cat, reasoning, confidence, method, categories_obj):
        tx.suggested_category_name = suggested_cat
        tx.reasoning = reasoning
        tx.confidence = confidence
        tx.status = 'pending_approval'
        
        # Reset deeper reasoning for non-AI matches (or we could clear them)
        tx.vendor_reasoning = reasoning
        tx.category_reasoning = f"Suggested based on {method} matching history."
        tx.tax_deduction_note = None
        
        # Resolve ID
        cat_obj = next((c for c in categories_obj if c.name == suggested_cat), None)
        if cat_obj:
            tx.suggested_category_id = cat_obj.id

        self.db.add(tx)

    def _apply_ai_suggestion(self, tx, analysis, categories_obj, category_list):
        print(f"🐛 [DEBUG] Applying AI analysis for tx {tx.id}. Keys received: {list(analysis.keys())}")
        print(f"🐛 [DEBUG] AI Reasoning payload: {analysis.get('reasoning')}")
        print(f"🐛 [DEBUG] tax_deduction_note payload: {analysis.get('tax_deduction_note')}")
        
        suggested_name = analysis.get('category')
        tx.suggested_category_name = suggested_name
        tx.reasoning = analysis.get('reasoning')
        tx.vendor_reasoning = analysis.get('vendor_reasoning')
        tx.category_reasoning = analysis.get('category_reasoning')
        tx.note_reasoning = analysis.get('note_reasoning')
        tx.tax_deduction_note = analysis.get('tax_deduction_note')
        tx.confidence = analysis.get('confidence')
        tx.status = 'unmatched' # Keep as unmatched so it shows in the list

        # Resolve ID (Exact or Fuzzy)
        if suggested_name:
            cat_match = categories_obj.get(suggested_name)
            if not cat_match:
                f_match = process.extractOne(suggested_name, category_list, scorer=fuzz.WRatio)
                if f_match and f_match[1] > 80:
                    cat_match = categories_obj.get(f_match[0])
            if cat_match:
                tx.suggested_category_id = cat_match.id

        # Capture AI Suggested Tags
        suggested_tags = analysis.get('tags', [])
        if suggested_tags:
            tx.suggested_tags = suggested_tags

        # Handle Splits
        splits_data = analysis.get('splits', [])
        if splits_data:
            tx.is_split = True
            for s in splits_data:
                s_cat_name = s['category']
                s_cat_match = next((c for c in categories_obj if c.name == s_cat_name), None)
                if not s_cat_match:
                    sf_match = process.extractOne(s_cat_name, category_list, scorer=fuzz.WRatio)
                    if sf_match and sf_match[1] > 80:
                        s_cat_match = next((c for c in categories_obj if c.name == sf_match[0]), None)
                
                split = TransactionSplit(
                    transaction_id=tx.id,
                    category_name=s_cat_name,
                    amount=s['amount'],
                    description=s.get('description') or tx.description
                )
                if s_cat_match:
                    split.category_id = s_cat_match.id
                
                tx.splits.append(split)
        
        self.db.add(tx)
