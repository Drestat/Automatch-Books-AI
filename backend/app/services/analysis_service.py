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
        Orchestrates hybrid intelligence:
        1. Deterministic Match (History)
        2. Generative AI (Gemini) via AIAnalyzer
        """
        print(f"🔍 [AnalysisService] Starting analysis for realm {self.realm_id}...")
        query = self.db.query(Transaction).filter(
            Transaction.realm_id == self.realm_id,
            Transaction.status == 'unmatched'
        )

        if tx_id:
            query = query.filter(Transaction.id == tx_id)
        
        unmatched = query.order_by(Transaction.date.desc()).limit(limit).all()
        
        print(f"🧠 [AnalysisService] Found {len(unmatched)} unmatched transactions to analyze (Limit: {limit})")

        if not unmatched:
            print("🧠 [AnalysisService] No unmatched transactions found.")
            return {"message": "No unmatched transactions found"}

        context = self.get_ai_context()
        categories_obj = context['category_objs']
        category_list = context['categories']
        vendor_mapping = context['vendor_mapping']
        
        results = []
        to_analyze_with_ai = unmatched # 100% AI Coverage requested by user
        
        if not to_analyze_with_ai:
            return results

        # --- Rule 2: AI Guess ---
        # Prepare context for AI
        history_str = "\\n".join([f"HISTORIC: '{desc}' -> Category: {cat}" for desc, cat in list(vendor_mapping.items())[:20]])
        ai_context = {
            "category_list": category_list,
            "history_str": history_str
        }

        # Token Logic
        from app.services.token_service import TokenService
        token_service = TokenService(self.db)
        
        # Determine cost (e.g., 1 token per transaction)
        cost_per_tx = 1
        total_cost = len(to_analyze_with_ai) * cost_per_tx
        
        user_id = self.db.query(QBOConnection).filter(QBOConnection.realm_id == self.realm_id).first().user_id
        
        if not token_service.has_sufficient_tokens(user_id, total_cost):
            # Partial processing or hard stop? Let's do partial or just return limitation message
            # For now, let's hard stop or process what we can
            available = token_service.get_balance(user_id)
            can_process_count = available // cost_per_tx
            if can_process_count == 0:
                return {"message": "Insufficient tokens for AI analysis. Please upgrade or wait for refresh."}
            
            to_analyze_with_ai = to_analyze_with_ai[:can_process_count]
            total_cost = can_process_count * cost_per_tx
            # Log warning or return info
            print(f"⚠️ Limited AI analysis to {can_process_count} transactions due to token balance.")

        try:
            # Deduct tokens upfront
            token_service.deduct_tokens(user_id, total_cost, reason=f"AI Analysis: {len(to_analyze_with_ai)} txs")
            
            analyses = self.analyzer.analyze_batch(to_analyze_with_ai, ai_context)
            
            # Robust mapping: Ensure ID is string to match DB text column
            analysis_map = {}
            for a in analyses:
                if 'id' in a:
                    analysis_map[str(a['id'])] = a

            print(f"🧠 [AnalysisService] AI returned {len(analyses)} analyses. Map keys: {list(analysis_map.keys())}")

            for tx in to_analyze_with_ai:
                # DB ID is string, so we lookup with string
                analysis = analysis_map.get(str(tx.id))
                if analysis:
                    self._apply_ai_suggestion(tx, analysis, categories_obj, category_list)
                    results.append({"id": tx.id, "analysis": {**analysis, "method": "ai"}})
                else:
                    print(f"⚠️ [AnalysisService] No AI analysis found for tx: {tx.description} ({tx.id}) - Expected ID: {tx.id}")
            
            self.db.commit()
            print(f"✅ [AnalysisService] AI enrichment complete for {len(results)} transactions.")
            self._log("ai_analysis", "transaction", len(results), "success")
            return results
        except Exception as e:
            # Refund if failed? In complex systems yes, here simplification
            print(f"❌ Batch AI Error: {str(e)}")
            if results: return results
            return {"error": str(e)}

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
