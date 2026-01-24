import requests
import json
import time
from datetime import datetime
from sqlalchemy.orm import Session
import google.generativeai as genai
from rapidfuzz import process, fuzz
from app.models.qbo import Transaction, QBOConnection, Category, Customer, SyncLog
from app.core.config import settings
from app.core.prompts import TRANSACTION_ANALYSIS_PROMPT, RECEIPT_ANALYSIS_PROMPT
from intuitlib.client import AuthClient

class SyncService:
    def __init__(self, db: Session, qbo_connection: QBOConnection):
        self.db = db
        self.connection = qbo_connection
        self.session = requests.Session()
        self.auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            redirect_uri=settings.QBO_REDIRECT_URI,
            environment=settings.QBO_ENVIRONMENT,
            refresh_token=self.connection.refresh_token,
            realm_id=self.connection.realm_id
        )
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.model = None

    def _log(self, operation: str, entity_type: str, count: int, status: str, details: dict = None):
        log = SyncLog(
            realm_id=self.connection.realm_id,
            operation=operation,
            entity_type=entity_type,
            count=count,
            status=status,
            details=details
        )
        self.db.add(log)
        self.db.commit()

    def sync_all(self):
        """Syncs all entities for the current connection"""
        self.sync_categories()
        self.sync_customers()
        self.sync_transactions()

    def _refresh_access_token(self):
        self.auth_client.refresh()
        self.connection.access_token = self.auth_client.access_token
        self.connection.refresh_token = self.auth_client.refresh_token
        self.db.add(self.connection)
        self.db.commit()
        return self.auth_client.access_token

    def _get_api_url(self, endpoint):
        base_url = "https://sandbox-quickbooks.api.intuit.com" if settings.QBO_ENVIRONMENT == "sandbox" else "https://quickbooks.api.intuit.com"
        return f"{base_url}/v3/company/{self.connection.realm_id}/{endpoint}"

    def _request_qbo(self, method: str, endpoint: str, params: dict = None, json_payload: dict = None):
        """
        Unified QBO request handler with:
        - Auto-refresh for 401 Unauthorized
        - Exponential backoff for 429 Rate Limits
        - Session reuse for performance
        """
        url = self._get_api_url(endpoint)
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            # Use self.session for connection pooling
            res = self.session.request(method, url, headers=headers, params=params, json=json_payload)
            
            if res.status_code == 401:
                token = self._refresh_access_token()
                headers['Authorization'] = f'Bearer {token}'
                continue # Retry with new token
            
            if res.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"⚠️ QBO Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            res.raise_for_status()
            return res.json()

    def _query_qbo(self, query_str):
        return self._request_qbo("GET", "query", params={'query': query_str})

    def sync_transactions(self):
        data = self._query_qbo("SELECT * FROM Purchase")
        purchases = data.get("QueryResponse", {}).get("Purchase", [])
        for p in purchases:
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
            
            tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
            tx.description = p.get("AccountRef", {}).get("name", "Purchased Item")
            tx.amount = p.get("TotalAmt", 0)
            tx.currency = p.get("CurrencyRef", {}).get("value", "USD")
            tx.raw_json = p
            self.db.add(tx)
        self.db.commit()
        self._log("sync", "transaction", len(purchases), "success")

    def sync_categories(self):
        data = self._query_qbo("SELECT * FROM Account WHERE AccountType = 'Expense'")
        accounts = data.get("QueryResponse", {}).get("Account", [])
        for a in accounts:
            cat = self.db.query(Category).filter(Category.id == a["Id"]).first()
            if not cat:
                cat = Category(id=a["Id"], realm_id=self.connection.realm_id)
            cat.name = a["Name"]
            cat.type = a["AccountType"]
            self.db.add(cat)
        self.db.commit()
        self._log("sync", "category", len(accounts), "success")

    def sync_customers(self):
        data = self._query_qbo("SELECT * FROM Customer")
        customers = data.get("QueryResponse", {}).get("Customer", [])
        for c in customers:
            cust = self.db.query(Customer).filter(Customer.id == c["Id"]).first()
            if not cust:
                cust = Customer(id=c["Id"], realm_id=self.connection.realm_id)
            cust.display_name = c["DisplayName"]
            cust.fully_qualified_name = c["FullyQualifiedName"]
            self.db.add(cust)
        self.db.commit()
        self._log("sync", "customer", len(customers), "success")

    def get_ai_context(self):
        """Fetches categories and customers for AI context"""
        categories = self.db.query(Category).filter(Category.realm_id == self.connection.realm_id).all()
        customers = self.db.query(Customer).filter(Customer.realm_id == self.connection.realm_id).all()
        
        # Vendor history context: Most frequent categories per description pattern
        # This is a simplified version of "Vendor Mapping"
        history = self.db.query(
            Transaction.description, 
            Transaction.suggested_category_name
        ).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.status == 'approved'
        ).all()
        
        vendor_mapping = {}
        for desc, cat in history:
            if desc not in vendor_mapping:
                vendor_mapping[desc] = cat

        return {
            "categories": [c.name for c in categories],
            "customers": [c.display_name for c in customers],
            "vendor_mapping": vendor_mapping
        }

    def analyze_transactions(self, limit: int = 20, tx_id: str = None):
        """
        Uses hybrid intelligence to categorize transactions:
        1. Deterministic Match (History)
        2. Generative AI (Gemini)
        """
        if not self.model:
            return {"error": "Gemini API Key missing"}

        query = self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.status == 'unmatched'
        )

        if tx_id:
            query = query.filter(Transaction.id == tx_id)
        
        # Order by date DESC to prioritize newest
        unmatched = query.order_by(Transaction.date.desc()).limit(limit).all()

        if not unmatched:
            return {"message": "No unmatched transactions found"}

        context = self.get_ai_context()
        vendor_mapping = context['vendor_mapping']
        
        results = []
        to_analyze_with_ai = []

        # --- Rule 1: Hybrid Match (Deterministic + Fuzzy History) ---
        for tx in unmatched:
            # First try exact match
            if tx.description in vendor_mapping:
                confidence = 1.0
                suggested_cat = vendor_mapping[tx.description]
                method = "deterministic"
                reasoning = f"Exact match with history for '{tx.description}'"
            else:
                # Try fuzzy match against history
                history_descriptions = list(vendor_mapping.keys())
                if history_descriptions:
                    match = process.extractOne(tx.description, history_descriptions, scorer=fuzz.WRatio)
                    if match and match[1] > 85: # 85% confidence threshold for history
                        suggested_cat = vendor_mapping[match[0]]
                        confidence = match[1] / 100
                        method = "fuzzy-history"
                        reasoning = f"Fuzzy match ( {int(match[1])}% ) with historic vendor '{match[0]}'"
                    else:
                        suggested_cat = None
                else:
                    suggested_cat = None

            if suggested_cat:
                tx.suggested_category_name = suggested_cat
                # Try to find the category ID by name
                cat_obj = self.db.query(Category).filter(
                    Category.name == suggested_cat,
                    Category.realm_id == self.connection.realm_id
                ).first()
                if cat_obj:
                    tx.suggested_category_id = cat_obj.id

                tx.reasoning = reasoning
                tx.confidence = confidence
                tx.status = 'pending_approval'
                
                self.db.add(tx)
                results.append({
                    "id": tx.id, 
                    "analysis": {
                        "suggested_category": suggested_cat, 
                        "reasoning": tx.reasoning, 
                        "confidence": confidence,
                        "method": method
                    }
                })
            else:
                to_analyze_with_ai.append(tx)
        
        self.db.commit() # Commit matches immediately

        # If no transactions left for AI, return early
        if not to_analyze_with_ai:
            return results

        # --- Rule 2: AI Guess (Gemini) ---
        
        # We provide ALL categories if the list is reasonable (Gemini 1.5 Pro handles this easily)
        categories_obj = self.db.query(Category).filter(Category.realm_id == self.connection.realm_id).all()
        category_list = [c.name for c in categories_obj]
        
        # Token Optimization: Prune history but provide high-signal examples
        history_list = list(vendor_mapping.items())[:20]
        
        tx_list_str = "\n".join([
            f"ID:{tx.id}|Desc:{tx.description}|Amt:{tx.amount} {tx.currency}" 
            for tx in to_analyze_with_ai
        ])

        history_str = "\n".join([
            f"HISTORIC: '{desc}' -> Category: {cat}" 
            for desc, cat in history_list
        ])

        prompt = TRANSACTION_ANALYSIS_PROMPT.format(
            category_list=', '.join(category_list),
            history_str=history_str,
            tx_list_str=tx_list_str
        )
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            analyses = json.loads(raw_text)
            
            analysis_map = {a['id']: a for a in analyses}
            
            for tx in to_analyze_with_ai:
                analysis = analysis_map.get(tx.id)
                if analysis:
                    suggested_name = analysis.get('suggested_category')
                    tx.suggested_category_name = suggested_name
                    tx.reasoning = analysis.get('reasoning')
                    tx.confidence = analysis.get('confidence')
                    tx.status = 'pending_approval'

                    # RESOLVE: Map suggested name to ID (Fuzzy match against real categories)
                    if suggested_name:
                        # Exact match first
                        cat_match = next((c for c in categories_obj if c.name == suggested_name), None)
                        if not cat_match:
                            # Fuzzy match against valid category names
                            f_match = process.extractOne(suggested_name, category_list, scorer=fuzz.WRatio)
                            if f_match and f_match[1] > 80:
                                cat_match = next((c for c in categories_obj if c.name == f_match[0]), None)
                        
                        if cat_match:
                            tx.suggested_category_id = cat_match.id

                    # --- Handle Splits ---
                    splits_data = analysis.get('splits', [])
                    if splits_data:
                        from app.models.qbo import TransactionSplit
                        tx.is_split = True
                        for s in splits_data:
                            # Resolve split category
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
                    results.append({
                        "id": tx.id, 
                        "analysis": {**analysis, "method": "ai"}
                    })
                else:
                    print(f"⚠️ No analysis returned for TX {tx.id}")
            
            self.db.commit()
            self._log("ai_analysis", "transaction", len(results), "success")
            return results
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            # Return partial results if deterministic matches worked but AI failed
            if results: 
                return results
            return {"error": str(e)}

    def approve_transaction(self, tx_id: str):
        """Finalizes a transaction and writes it back to QBO"""
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")

        # Update QBO via API
        payload = tx.raw_json
        
        if tx.is_split and tx.splits:
            # Multi-line split logic
            new_lines = []
            for s in tx.splits:
                line = {
                    "Description": s.description,
                    "Amount": float(s.amount),
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {
                            "value": s.category_id,
                            "name": s.category_name
                        }
                    }
                }
                new_lines.append(line)
            payload["Line"] = new_lines
        else:
            # Single category logic
            if not tx.suggested_category_id:
                 raise ValueError("Transaction has no suggested category")
            
            if "Line" in payload and len(payload["Line"]) > 0:
                # Update first line (standard QBO Purchase pattern)
                payload["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"] = {
                    "value": tx.suggested_category_id,
                    "name": tx.suggested_category_name
                }
            else:
                # Fallback to main AccountRef if lines are missing (rare)
                payload["AccountRef"] = {"value": tx.suggested_category_id, "name": tx.suggested_category_name}
        
        res_data = self._request_qbo("POST", "purchase", params={'operation': 'update'}, json_payload=payload)

        # Update Mirror Status
        tx.status = 'approved'
        self.db.add(tx)
        self.db.commit()
        
        self._log("approve", "transaction", 1, "success", {"tx_id": tx_id})
        return res_data

    def bulk_approve(self, tx_ids: list[str]):
        """Approves multiple transactions in a batch"""
        results = []
        for tx_id in tx_ids:
            try:
                res = self.approve_transaction(tx_id)
                results.append({"id": tx_id, "status": "success"})
            except Exception as e:
                results.append({"id": tx_id, "status": "error", "message": str(e)})
        
        success_count = len([r for r in results if r["status"] == "success"])
        self._log("bulk_approve", "transaction", success_count, "partial" if success_count < len(tx_ids) else "success", {"results": results})
        return results

    def process_receipt(self, file_content: bytes, filename: str):
        """
        Uses Gemini Vision to read a receipt and find the best transaction match.
        """
        # 1. Identify Receipt Content
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        prompt = RECEIPT_ANALYSIS_PROMPT
        
        # Prepare for Gemini
        vision_result = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": file_content}
        ])
        
        try:
            raw_text = vision_result.text.replace('```json', '').replace('```', '').strip()
            extracted = json.loads(raw_text)
        except Exception as e:
            print(f"❌ AI Receipt Error: {str(e)}")
            raise ValueError("Could not parse receipt data from AI")

        # 2. Find Best Match in recent transactions
        amount = float(extracted.get('total', 0))
        txs = self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.status == 'unmatched'
        ).all()
        
        best_match = None
        for tx in txs:
            merchant_score = fuzz.WRatio(extracted.get('merchant', ''), tx.description)
            # Use abs(tx.amount) because bank feed often has negative for expenses
            amount_diff = abs(abs(float(tx.amount)) - amount)
            
            if merchant_score > 70 and amount_diff < (amount * 0.1):
                best_match = tx
                break
        
        return {
            "extracted": extracted,
            "match": best_match
        }
