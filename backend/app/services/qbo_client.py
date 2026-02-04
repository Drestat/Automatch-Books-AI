import httpx
import asyncio
from sqlalchemy.orm import Session
from app.models.qbo import QBOConnection
from app.core.config import settings
from intuitlib.client import AuthClient

class QBOClient:
    def __init__(self, db: Session, qbo_connection: QBOConnection):
        self.db = db
        self.connection = qbo_connection
        # We keep AuthClient for token management, even if we use httpx for requests
        self.auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            redirect_uri=settings.QBO_REDIRECT_URI,
            environment=settings.QBO_ENVIRONMENT,
            refresh_token=self.connection.refresh_token,
            realm_id=self.connection.realm_id
        )

    def _refresh_access_token(self):
        # AuthClient is synchronous. In a rigorous async app, we might wrap this 
        # or use an async-compatible auth library. usage: blocking for now.
        print("🔄 [QBOClient] Refreshing Access Token...")
        self.auth_client.refresh()
        self.connection.access_token = self.auth_client.access_token
        self.connection.refresh_token = self.auth_client.refresh_token
        self.db.add(self.connection)
        self.db.commit()
        return self.auth_client.access_token

    def _get_api_url(self, endpoint):
        base_url = "https://sandbox-quickbooks.api.intuit.com" if settings.QBO_ENVIRONMENT == "sandbox" else "https://quickbooks.api.intuit.com"
        return f"{base_url}/v3/company/{self.connection.realm_id}/{endpoint}"

    async def request(self, method: str, endpoint: str, params: dict = None, json_payload: dict = None):
        """
        Async Unified QBO request handler with:
        - Auto-refresh for 401 Unauthorized
        - Exponential backoff for 429 Rate Limits
        - httpx.AsyncClient for non-blocking I/O
        """
        url = self._get_api_url(endpoint)
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        backoff_factor = 2
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    res = await client.request(method, url, headers=headers, params=params, json=json_payload)
                    
                    if res.status_code == 401:
                        # Refresh logic (blocking DB write, but acceptable for rare auth refresh)
                        token = self._refresh_access_token() 
                        headers['Authorization'] = f'Bearer {token}'
                        continue 
                    
                    if res.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = backoff_factor ** attempt
                            print(f"⚠️ QBO Rate Limit (429). Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    res.raise_for_status()
                    return res.json()
                    
                except httpx.RequestError as e:
                    print(f"❌ [QBOClient] Network Error: {e}")
                    raise
                except httpx.HTTPStatusError as e:
                    print(f"❌ [QBOClient] HTTP Error: {e.response.text}")
                    raise

    async def query(self, query_str):
        return await self.request("GET", "query", params={'query': query_str})

    async def update_purchase(self, purchase_id: str, category_id: str, category_name: str, sync_token: str, entity_ref: dict = None, payment_type: str = None):
        """
        Update a Purchase entity (Expense/Check) via Sparse Update.
        """
        update_payload = {
            "Id": purchase_id,
            "SyncToken": sync_token,
            "sparse": True,
            "Line": [
                {
                    "Id": "1", 
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {
                            "value": category_id,
                            "name": category_name
                        }
                    }
                }
            ]
        }
        
        if entity_ref:
            update_payload["EntityRef"] = entity_ref
            
        if payment_type:
            update_payload["PaymentType"] = payment_type

        print(f"📝 [QBOClient] Updating Purchase {purchase_id} -> Cat: {category_name}, Payee: {entity_ref.get('name') if entity_ref else 'N/A'}, PayType: {payment_type}")
        result = await self.request("POST", "purchase", json_payload=update_payload)
        return result.get("Purchase", {})

    async def create_bill_payment(self, bill_id: str, bank_account_id: str, amount: float, date: str):
        """
        Create a BillPayment (Check) to link a Bill to a bank withdrawal.
        This confirms the match in QBO.
        """
        payload = {
            "TxnDate": date,
            "PayType": "Check", 
            "CheckPayment": {
                "BankAccountRef": {"value": bank_account_id}
            },
            "Line": [
                {
                    "Amount": amount,
                    "LinkedTxn": [
                         {"TxnId": bill_id, "TxnType": "Bill"}
                    ]
                }
            ]
        }
        print(f"📝 [QBOClient] Creating BillPayment for Bill {bill_id}")
        result = await self.request("POST", "billpayment", json_payload=payload)
        return result.get("BillPayment", {})

    async def create_vendor(self, vendor_name: str):
        payload = {"DisplayName": vendor_name}
        print(f"📝 [QBOClient] Creating vendor: {vendor_name}")
        result = await self.request("POST", "vendor", json_payload=payload)
        return result.get("Vendor", {})

    async def get_vendor_by_name(self, vendor_name: str):
        """Searches for a vendor by display name in QBO."""
        # Escape single quotes in vendor_name for SQL-like query
        safe_name = vendor_name.replace("'", "\\'")
        query = f"SELECT * FROM Vendor WHERE DisplayName = '{safe_name}'"
        print(f"🔍 [QBOClient] Searching for vendor: {vendor_name}")
        result = await self.query(query)
        vendors = result.get("QueryResponse", {}).get("Vendor", [])
        return vendors[0] if vendors else None

    def revoke(self):
        try:
            print(f"🔌 [QBOClient] Revoking token...")
            self.auth_client.revoke(token=self.connection.refresh_token)
            return True
        except Exception:
            return False
