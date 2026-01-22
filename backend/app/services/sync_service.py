import os
import json
import requests
from datetime import datetime
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.models.qbo import Transaction, QBOConnection, Category, Customer

class SyncService:
    def __init__(self, db: Session, qbo_connection: QBOConnection):
        self.db = db
        self.connection = qbo_connection
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
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

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

    def _query_qbo(self, query_str):
        url = self._get_api_url("query")
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json'
        }
        res = requests.get(url, headers=headers, params={'query': query_str})
        if res.status_code == 401:
            token = self._refresh_access_token()
            headers['Authorization'] = f'Bearer {token}'
            res = requests.get(url, headers=headers, params={'query': query_str})
        res.raise_for_status()
        return res.json()

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
        """Uses Gemini to analyze unmatched transactions in batches or individually"""
        if not self.model:
            return {"error": "Gemini API Key missing"}

        query = self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.status == 'unmatched'
        )

        if tx_id:
            query = query.filter(Transaction.id == tx_id)
        
        unmatched = query.order_by(Transaction.date.desc()).limit(limit).all()

        if not unmatched:
            return {"message": "No unmatched transactions found"}

        context = self.get_ai_context()
        
        # Token Optimization: Prune context to essential data
        # Only send top 35 categories and top 15 history mappings
        category_list = context['categories'][:35]
        history_list = list(context['vendor_mapping'].items())[:15]
        
        tx_list_str = "\n".join([
            f"ID:{tx.id}|Desc:{tx.description}|Amt:{tx.amount}" 
            for tx in unmatched
        ])

        history_str = "\n".join([
            f"{desc}->{cat}" 
            for desc, cat in history_list
        ])

        prompt = f"""
        Categorize these bank transactions for QuickBooks. 
        Be efficient. Use only these categories: {', '.join(category_list)}
        
        Recent mappings:
        {history_str}
        
        Transactions:
        {tx_list_str}
        
        Output JSON list. 
        'reasoning' MUST be < 15 words.
        [
            {{"id": "...", "suggested_category": "...", "reasoning": "...", "confidence": 0.0}}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Remove markdown formatting if present
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            analyses = json.loads(raw_text)
            
            # Map results back to transactions
            analysis_map = {a['id']: a for a in analyses}
            
            results = []
            for tx in unmatched:
                analysis = analysis_map.get(tx.id)
                if analysis:
                    tx.suggested_category_name = analysis.get('suggested_category')
                    tx.reasoning = analysis.get('reasoning')
                    tx.confidence = analysis.get('confidence')
                    tx.status = 'pending_approval'
                    self.db.add(tx)
                    results.append({"id": tx.id, "analysis": analysis})
                else:
                    print(f"⚠️ No analysis returned for TX {tx.id}")
            
            self.db.commit()
            return results
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            return {"error": str(e)}

    def approve_transaction(self, tx_id: str):
        """Finalizes a transaction and writes it back to QBO"""
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx or not tx.suggested_category_id:
            raise ValueError(f"Transaction {tx_id} not found or has no suggested category")

        # 1. Update QBO via API
        url = self._get_api_url("purchase")
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # We use the raw_json stored in Postgres
        payload = tx.raw_json
        payload["AccountRef"] = {"value": tx.suggested_category_id, "name": tx.suggested_category_name}
        
        res = requests.post(url, headers=headers, json=payload, params={'operation': 'update'})
        if res.status_code == 401:
            token = self._refresh_access_token()
            headers['Authorization'] = f'Bearer {token}'
            res = requests.post(url, headers=headers, json=payload, params={'operation': 'update'})
        
        res.raise_for_status()

        # 2. Update Mirror Status
        tx.status = 'approved'
        self.db.add(tx)
        self.db.commit()
        
        return res.json()
