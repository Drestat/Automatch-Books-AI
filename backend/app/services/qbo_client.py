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

    async def get_entity(self, entity_id: str, entity_type: str = "Purchase"):
        """Fetches a single entity by ID using the correct endpoint."""
        type_mapping = {
            "Purchase": "purchase",
            "Expense": "purchase",
            "BillPayment": "billpayment",
            "Deposit": "deposit",
            "JournalEntry": "journalentry",
            "Transfer": "transfer",
            "CreditCardCredit": "purchase",
            "Check": "purchase",
            "Payment": "payment",
            "SalesReceipt": "salesreceipt",
            "RefundReceipt": "refundreceipt",
            "CreditMemo": "creditmemo",
            "Bill": "bill",
            "Invoice": "invoice"
        }
        endpoint = type_mapping.get(entity_type, "purchase")
        return await self.request("GET", f"{endpoint}/{entity_id}")

    async def get_purchase(self, purchase_id: str):
        """Fetches a single Purchase entity by ID (Legacy wrapper)."""
        return await self.get_entity(purchase_id, "Purchase")

    async def update_purchase(self, purchase_id: str, category_id: str, category_name: str, sync_token: str, entity_type: str = "Purchase", entity_ref: dict = None, payment_type: str = None, txn_status: str = None, global_tax_calculation: str = None, existing_line_override: dict = None, tags: list[str] = None, note: str = None, description: str = None, append_memo: str = None, deposit_to_account_ref: dict = None, from_account_ref: dict = None):
        """
        Update a QBO entity (Purchase, BillPayment, etc.) via Sparse Update.
        Preserves existing line details if 'existing_line_override' is provided.
        IMPORTANT: Never overwrites Date or Amount.
        """
        
        # Determine endpoint (handle legacy 'Expense' and other types)
        type_mapping = {
            "Purchase": "purchase",
            "Expense": "purchase", # Legacy support
            "BillPayment": "billpayment",
            "Deposit": "deposit",
            "JournalEntry": "journalentry",
            "Transfer": "transfer",
            "CreditCardCredit": "purchase",
            "Check": "purchase",
            "Payment": "payment",
            "SalesReceipt": "salesreceipt",
            "RefundReceipt": "refundreceipt",
            "CreditMemo": "creditmemo"
        }
        endpoint = type_mapping.get(entity_type, "purchase").lower()
        
        # Determine DetailType based on Entity Type
        detail_type = "AccountBasedExpenseLineDetail"
        if entity_type == "Deposit":
            detail_type = "DepositLineDetail"
        elif entity_type == "JournalEntry":
            detail_type = "JournalEntryLineDetail"
        elif entity_type == "BillPayment":
            detail_type = "BillPaymentLineDetail"
        elif entity_type in ["SalesReceipt", "RefundReceipt", "CreditMemo"]:
            detail_type = "SalesItemLineDetail"

        # Prepare Line Item
        update_line = False
        line_item = {}
        if existing_line_override:
            update_line = True
            line_item = existing_line_override
            # Purge invalid fields if they exist
            if "ClrStatus" in line_item:
                del line_item["ClrStatus"]
            
            # Ensure DetailType is correct for the specific entity
            if entity_type != "BillPayment":
                line_item["DetailType"] = detail_type
                if detail_type not in line_item:
                    line_item[detail_type] = {}
        elif category_id:
            update_line = True
            line_item = {
                "Id": "1", 
                "DetailType": detail_type,
                detail_type: {}
            }

        # Update Category (Account) - Only if it's NOT a BillPayment or Payment
        if update_line and category_id and entity_type not in ["BillPayment", "Payment"]:
            # Note: For RefundReceipt/SalesReceipt, QBO requires an ItemRef, not an AccountRef directly.
            # ItemAccountRef is only for Invoice-related reimbursements.
            if detail_type == "SalesItemLineDetail":
                if entity_type == "Invoice":
                    line_item[detail_type]["ItemAccountRef"] = {
                        "value": category_id,
                        "name": category_name
                    }
                else:
                    # For SalesReceipt/RefundReceipt, we fallback to ItemRef as AccountRef isn't allowed.
                    # This is better than sending an invalid field that causes a 400.
                    # Future: Map Category to a QBO Service Item.
                    pass 
            else:
                line_item[detail_type]["AccountRef"] = {
                    "value": category_id,
                    "name": category_name
                }
        
        # Description Override logic
        if update_line and description:
            line_item["Description"] = description
        
        # NEVER set line_item["Amount"] here. We want to preserve the bank amount.
        
        update_payload = {
            "Id": purchase_id,
            "SyncToken": sync_token,
            "sparse": True
        }

        if update_line and entity_type not in ["BillPayment", "Payment"]:
            update_payload["Line"] = [line_item]

        # Date (TxnDate) and TotalAmt are EXCLUDED to prevent accidental overwrites.
        
        if entity_ref:
            if endpoint == "purchase":
                update_payload["EntityRef"] = entity_ref
            elif endpoint in ["salesreceipt", "refundreceipt", "creditmemo"]:
                update_payload["CustomerRef"] = entity_ref
            # elif endpoint == "payment":
            #    update_payload["CustomerRef"] = entity_ref
            #    NOTE: Sending CustomerRef in a sparse update for Payment often triggers 
            #    "You can't link a payment from a sub customer..." errors if the invoice linkage isn't perfect.
            #    For standard "Approve" actions (updating memo/status), we should SKIP CustomerRef for Payments.

        if deposit_to_account_ref:
            update_payload["DepositToAccountRef"] = deposit_to_account_ref
        
        if from_account_ref:
            update_payload["FromAccountRef"] = from_account_ref

        if payment_type and endpoint == "purchase":
            update_payload["PaymentType"] = payment_type
            
        if txn_status and endpoint == "purchase":
            update_payload["TxnStatus"] = txn_status
            
        if global_tax_calculation and endpoint == "purchase":
            update_payload["GlobalTaxCalculation"] = global_tax_calculation

        # PrivateNote (Memo) logic: Combine Description + Note + Tags + AppendMemo
        memo_parts = []
        
        # for Payments/BillPayments, the Description must live in the Memo/PrivateNote
        # because we often skip Line updates or they don't have a header Description.
        if description and entity_type in ["Payment", "BillPayment"]:
            memo_parts.append(description)

        if note:
            memo_parts.append(note)
            
        if tags:
            tag_str = ", ".join([f"#{t}" for t in tags if t])
            memo_parts.append(f"Tags: {tag_str}")
        
        if append_memo:
            memo_parts.append(append_memo)

        if memo_parts:
            # BillPayment seems to prefer PrivateNote in some contexts, let's standardize
            memo_text = " | ".join(memo_parts)
            update_payload["PrivateNote"] = memo_text
            
            # For Sales types, also set CustomerMemo to ensure it shows up in most UI views
            if endpoint in ["salesreceipt", "refundreceipt", "creditmemo", "invoice"]:
                update_payload["CustomerMemo"] = {"value": memo_text}

        print(f"📝 [QBOClient] Updating {entity_type} {purchase_id} -> Endpoint: {endpoint}")
        
        result = await self.request("POST", endpoint, json_payload=update_payload)
        
        # Robust result extraction:
        # 1. Try explicit entity_type (e.g. SalesReceipt)
        # 2. Try PascalCase (e.g. SalesReceipt)
        # 3. Try "Purchase" fallback (for Expenses)
        # 4. Filter by any key that has an 'Id'
        obj = result.get(entity_type)
        if not obj:
            # Try lower case and capitalize for safety
            obj = result.get(entity_type.capitalize())
        if not obj and endpoint == "purchase":
            obj = result.get("Purchase")
        
        if not obj:
            for k, v in result.items():
                if isinstance(v, dict) and "Id" in v:
                    obj = v
                    break
        
        return obj or {}

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

    async def get_customer_by_name(self, customer_name: str):
        """Searches for a customer by display name in QBO."""
        # Escape single quotes in customer_name for SQL-like query
        safe_name = customer_name.replace("'", "\\'")
        query = f"SELECT * FROM Customer WHERE DisplayName = '{safe_name}'"
        print(f"🔍 [QBOClient] Searching for customer: {customer_name}")
        result = await self.query(query)
        customers = result.get("QueryResponse", {}).get("Customer", [])
        return customers[0] if customers else None

    async def upload_attachment(self, file_bytes: bytes, filename: str, content_type: str, attachable_ref: dict = None):
        """
        Uploads a file to QBO 'Attachable' endpoint using multipart/form-data.
        Docs: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/attachable#upload-attachments
        """
        endpoint = "upload"
        url = self._get_api_url(endpoint)
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json'
            # Content-Type is set automatically by httpx for multipart
        }
        
        # Metadata part (JSON)
        metadata = {
            "ContentType": content_type,
            "FileName": filename
        }
        if attachable_ref:
            # Setup linking (e.g. to a Purchase)
            # Structure: "AttachableRef": [{"EntityRef": {"type": "Purchase", "value": "123"}}]
            metadata["AttachableRef"] = [attachable_ref]

        import json
        
        # httpx expects 'files' for multipart
        # QBO requires specific part names: 'file_metadata_01' and 'file_content_01'
        files = {
            'file_metadata_01': (None, json.dumps(metadata), 'application/json'),
            'file_content_01': (filename, file_bytes, content_type)
        }
        
        print(f"Tb [QBOClient] Uploading attachment: {filename} ({len(file_bytes)} bytes)")
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, headers=headers, files=files)
                if res.status_code == 401:
                    # Simple refresh retry (blocking)
                    token = self._refresh_access_token()
                    headers['Authorization'] = f'Bearer {token}'
                    res = await client.post(url, headers=headers, files=files)
                
                res.raise_for_status()
                result = res.json()
                return result.get("AttachableResponse", [{}])[0].get("Attachable", {})
                
            except httpx.HTTPStatusError as e:
                print(f"❌ [QBOClient] Upload Failed: {e.response.text}")
                raise e

    def revoke(self):
        try:
            print(f"🔌 [QBOClient] Revoking token...")
            self.auth_client.revoke(token=self.connection.refresh_token)
            return True
        except Exception:
            return False
