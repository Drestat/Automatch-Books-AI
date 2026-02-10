from sqlalchemy.orm import Session
from rapidfuzz import process, fuzz
from app.models.qbo import Transaction, Category, Customer, TransactionSplit, SyncLog, QBOConnection, VendorAlias, ClassificationRule
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
        """Fetches categories, entities (customers/vendors) for AI context"""
        categories = self.db.query(Category).filter(Category.realm_id == self.realm_id).all()
        customers = self.db.query(Customer).filter(Customer.realm_id == self.realm_id).all()
        from app.models.qbo import Vendor
        vendors = self.db.query(Vendor).filter(Vendor.realm_id == self.realm_id).all()
        
        # Entity Vocabulary (Prioritize FullyQualifiedName)
        entity_vocabulary = []
        for c in customers:
            entity_vocabulary.append(c.fully_qualified_name or c.display_name)
        for v in vendors:
            entity_vocabulary.append(v.fully_qualified_name or v.display_name)
        
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
            if desc and desc not in vendor_mapping:
                vendor_mapping[desc] = cat

        return {
            "categories": [c.name for c in categories],
            "entity_vocabulary": entity_vocabulary,
            "vendor_mapping": vendor_mapping,
            "category_objs": {c.name: c for c in categories}
        }

    def analyze_transactions(self, limit: int = 100, tx_id: str = None, allow_ai: bool = True):
        """
        Orchestrates hybrid intelligence with Rule-based logic and Gemini.
        allow_ai: If False, only runs deterministic rules and history matching (Free).
        """
        print(f"🔍 [AnalysisService] Starting analysis for realm {self.realm_id} (AI Enabled: {allow_ai})...")
        if tx_id:
            query = self.db.query(Transaction).filter(Transaction.id == tx_id, Transaction.realm_id == self.realm_id)
        else:
            query = self.db.query(Transaction).filter(
                Transaction.realm_id == self.realm_id,
                Transaction.status == 'unmatched'
            )
        
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
            # 0. Check Natural Language Rules (Highest Priority)
            if self._apply_rules(tx):
                 results.append({"id": tx.id, "analysis": {"category": tx.suggested_category_name, "method": "rule"}})
                 continue

            # 0.5. Check Vendor Aliases
            alias_vendor = self._resolve_vendor_alias(tx.description)
            if alias_vendor:
                print(f"🏷️ [Alias] Mapped '{tx.description}' to '{alias_vendor}'")
                # Update description or payee? Usually Payee.
                tx.payee = alias_vendor
                # We might want to re-check history with the new vendor name?
                # For now, let it flow to History/AI with the better Payee.
            
            # 1. History Match
            # Skip history match if we are explicitly analyzing a specific transaction (User Request)
            if not tx_id and tx.description in vendor_mapping:
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
        if not allow_ai:
            print("🛑 [AnalysisService] AI Analysis disabled by configuration. Returning deterministic results only.")
            self.db.commit()
            return results

        history_str = "\n".join([f"HISTORIC: '{desc}' -> Category: {cat}" for desc, cat in list(vendor_mapping.items())[:20]])
        ai_context = {
            "category_list": category_list, 
            "history_str": history_str,
            "entity_vocabulary": context.get('entity_vocabulary', [])
        }

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
            # Only deduct if this is a bulk run. If tx_id is set, API endpoint paid for it.
            if not tx_id:
                token_service.deduct_tokens(user_id, cost, reason=f"AI Analysis")
            else:
                print(f"🎟️ [Token] Skipping deduction for interactive analysis (Paid by API)")
            
            analyses = self.analyzer.analyze_batch(to_analyze_with_ai, ai_context)
            
            analysis_map = {str(a.get('id')): a for a in analyses if a.get('id')}

            for tx in to_analyze_with_ai:
                analysis = analysis_map.get(str(tx.id))
                if analysis:
                    self._apply_ai_suggestion(tx, analysis, categories_obj, category_list)
                    results.append({"id": tx.id, "analysis": {**analysis, "method": "ai"}})
                    
                    # --- Rule 3: Auto-Approve High Confidence (Founder/Empire Tier) ---
                    from app.models.user import User
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if tx.confidence and tx.confidence >= 0.95 and user and user.subscription_tier in ['founder', 'empire']:
                        print(f"🚀 [Auto-Approve] High confidence ({tx.confidence}) for {tx.id} (Tier: {user.subscription_tier})")
                        tx.status = 'pending_approval'
                    elif tx.confidence and tx.confidence >= 0.8:
                        tx.status = 'pending_approval'
                
            self.db.commit()
            return results
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            # Even on error, we might want to commit what we have
            self.db.commit()
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
        
        suggested_name = analysis.get('category')
        tx.suggested_category_name = suggested_name
        tx.suggested_payee = analysis.get('payee')
        
        tx.reasoning = analysis.get('reasoning')
        tx.vendor_reasoning = analysis.get('vendor_reasoning')
        tx.category_reasoning = analysis.get('category_reasoning')
        tx.note_reasoning = analysis.get('note_reasoning')
        tx.tax_deduction_note = analysis.get('tax_deduction_note')
        tx.confidence = analysis.get('confidence')
        tx.status = 'unmatched' # Keep as unmatched so it shows in the list

        # DESCRIPTION LOGIC: Removed auto-fill per user request (v3.28.17)
        # Frontend will handle suggestions if description is empty.

        # Resolve Suggested Category ID (Pre-Validation - SaasAnt Standard)
        if suggested_name:
            # 1. Strict Check
            cat_match = categories_obj.get(suggested_name)
            
            # 2. Fuzzy Fallback (if AI hallucinated a slightly different name)
            if not cat_match:
                f_match = process.extractOne(suggested_name, category_list, scorer=fuzz.WRatio)
                if f_match and f_match[1] > 85: # High threshold for safety
                    cat_match = categories_obj.get(f_match[0])
                    print(f"⚠️ [Validation] Fuzzy corrected '{suggested_name}' -> '{cat_match.name}'")
            
            if cat_match:
                tx.suggested_category_id = cat_match.id
                tx.suggested_category_name = cat_match.name # Force canonical name
            else:
                # 3. Validation Failure - Do NOT assign invalid category
                print(f"❌ [Validation] AI suggested invalid category '{suggested_name}'. Reverting to Uncategorized.")
                tx.suggested_category_id = None
                tx.suggested_category_name = None
                tx.category_reasoning = (tx.category_reasoning or "") + f" [Warning: AI suggested '{suggested_name}' which does not exist in QBO.]"
                tx.confidence = 0.4 # Penalize confidence

        # Capture AI Suggested Tags
        tx.suggested_tags = analysis.get('tags', [])

        # Handle Splits
        splits_data = analysis.get('splits', [])
        
        # IDEMPOTENCY FIX: Clear existing splits first (if any) to prevent duplication on re-run
        if splits_data or tx.splits:
            # Look for existing splits bound to this tx and delete them
            self.db.query(TransactionSplit).filter(TransactionSplit.transaction_id == tx.id).delete()
            tx.is_split = False # Reset flag, will set to True if new splits exist

        if splits_data:
            tx.is_split = True
            for s in splits_data:
                s_cat_name = s['category']
                # Use dict lookup (O(1)) instead of iteration
                s_cat_match = categories_obj.get(s_cat_name)
                
                if not s_cat_match:
                    sf_match = process.extractOne(s_cat_name, category_list, scorer=fuzz.WRatio)
                    if sf_match and sf_match[1] > 80:
                        s_cat_match = categories_obj.get(sf_match[0])
                
                split = TransactionSplit(
                    transaction_id=tx.id,
                    category_name=s_cat_name,
                    amount=s['amount'],
                    description=s.get('description') or tx.description
                )
                if s_cat_match:
                    split.category_id = s_cat_match.id
                
                self.db.add(split)
        
        self.db.add(tx)

    def _resolve_vendor_alias(self, description: str):
        """
        Dext-style Aliasing:
        "Amazon Mktp 123" -> "Amazon"
        """
        if not description: return None
        
        # Simple exact substring match for now. 
        # In a real app, this would be cached or more sophisticated.
        aliases = self.db.query(VendorAlias).filter(VendorAlias.realm_id == self.realm_id).all()
        for alias in aliases:
            if alias.alias.lower() in description.lower():
                # Fetch vendor name
                from app.models.qbo import Vendor
                vendor = self.db.query(Vendor).filter(Vendor.id == alias.vendor_id).first()
                if vendor:
                    return vendor.display_name
        return None

    def _apply_rules(self, tx):
        """
        Natural Language Rules Engine (Unique)
        Priority-based execution.
        """
        rules = self.db.query(ClassificationRule).filter(
            ClassificationRule.realm_id == self.realm_id
        ).order_by(ClassificationRule.priority.desc()).all()

        for rule in rules:
            conditions = rule.conditions
            match = True
            
            # 1. Description Contains
            if "description_contains" in conditions:
                if conditions["description_contains"].lower() not in (tx.description or "").lower():
                    match = False
            
            # 2. Amount Range (min/max)
            if "amount_min" in conditions:
                if abs(float(tx.amount)) < float(conditions["amount_min"]): match = False
            if "amount_max" in conditions:
                if abs(float(tx.amount)) > float(conditions["amount_max"]): match = False

            if match:
                print(f"✨ [Rules] Applied rule '{rule.name}' to {tx.id}")
                action = rule.action
                
                if "category" in action:
                    tx.suggested_category_name = action["category"]
                    # Resolve ID (quick lookup)
                    cat = self.db.query(Category).filter(
                        Category.realm_id == self.realm_id, 
                        Category.name == action["category"]
                    ).first()
                    if cat: tx.suggested_category_id = cat.id
                
                if "tag" in action:
                    current_tags = tx.tags or []
                    if action["tag"] not in current_tags:
                        current_tags.append(action["tag"])
                        tx.tags = current_tags

                tx.reasoning = f"Matched rule: {rule.name}"
                tx.confidence = 1.0 # Rules are absolute
                tx.status = 'pending_approval'
                return True
        
        # If no rule matched, return False so AI can take over
        return False
