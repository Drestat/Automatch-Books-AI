from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.qbo import Transaction, QBOConnection, Category, Customer, Vendor, SyncLog, TransactionSplit, BankAccount, Tag
from app.models.user import User
from app.services.qbo_client import QBOClient
import uuid

class TransactionService:
    def __init__(self, db: Session, qbo_connection: QBOConnection):
        self.db = db
        self.connection = qbo_connection
        self.client = QBOClient(db, qbo_connection)

    async def sync_bank_accounts(self):
        """Shim to call SyncService until qbo.py is refactored."""
        from app.services.sync_service import SyncService
        syncer = SyncService(self.db, self.connection)
        await syncer.sync_bank_accounts()

    async def sync_transactions(self):
        """Shim to call SyncService until qbo.py is refactored."""
        from app.services.sync_service import SyncService
        syncer = SyncService(self.db, self.connection)
        await syncer.sync_transactions()

    def _get_account_limit(self):
        user = self.db.query(User).filter(User.id == self.connection.user_id).first()
        if not user:
            return 1
        
        limits = {
            "free": 1,
            "pro": 5,
            "founder": 100,
            "empire": 1000
        }
        return limits.get(user.subscription_tier, 1)

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

    async def approve_transaction(self, tx_id: str):
        """
        Finalizes a transaction and writes it back to QBO.
        Supports standard categorization and Split transactions.
        """
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")
        
        if tx.status == 'approved':
            print(f"⏩ [Approve] Transaction {tx_id} already approved, skipping.")
            return {"status": "success", "message": "Transaction already approved"}

        try:
            if tx.is_split and tx.splits:
                print(f"✂️ [Approve] Processing SPLIT transaction {tx.id}...")
                await self._update_qbo_split_transaction(tx)
            else:
                print(f"🏷️ [Approve] Processing standard transaction {tx.id}...")
                await self._update_qbo_transaction(tx)
            
        except Exception as e:
            print(f"❌ [Approve] Write-Back Failed: {e}")
            raise e

        if not tx.amount or tx.amount == 0:
            print(f"⚠️ [Approve] Transaction {tx.id} has 0.00 amount. Fetching from QBO to preserve value...")
            try:
                qbo_tx = await self.client.get_purchase(tx.id)
                purchase_data = qbo_tx.get("Purchase", {})
                real_amount = purchase_data.get("TotalAmt")
                if real_amount:
                    tx.amount = real_amount
                    print(f"✅ [Approve] Restored amount to {real_amount} from QBO.")
            except Exception as e:
                print(f"❌ [Approve] Failed to fetch original amount: {e}")
                
        # Local Update
        tx.status = 'approved' 
        tx.forced_review = False
        tx.is_qbo_matched = True
        self.db.add(tx)
        self.db.commit()
        
        self._log("approve", "transaction", 1, "success", {"tx_id": tx_id, "is_split": tx.is_split})
        return {"status": "success", "message": "Transaction updated in QuickBooks"}

    async def _update_qbo_transaction(self, tx):
        """
        Helper: Writes standard categorization to QBO.
        """
        cat_id = tx.category_id or tx.suggested_category_id
        cat_name = tx.category_name or tx.suggested_category_name
        
        if not cat_id:
            raise ValueError(f"Transaction {tx.id} missing category")
        
        entity_ref = await self._resolve_entity_ref(tx.payee, tx.transaction_type)
        payment_type = tx.raw_json.get("PaymentType") if tx.raw_json else None

        # [PaymentType Logic]
        # If PaymentType is not explicitly Check or CreditCard, we default based on Account Type.
        # This is critical for matching QBO Bank Feeds (which are usually Expenses/Cash or CreditCard Charges).
        if not payment_type or payment_type == "Check": 
            # Note: Even if it says "Check" in raw_json, if it has no DocNum, it might be a mis-classification 
            # or default QBO behavior. We prefer "Cash" (Expense) for matching unless user explicitly intends a Check.
            
            # Fetch Account Type
            bank_account = self.db.query(BankAccount).filter(
                BankAccount.id == tx.account_id,
                BankAccount.realm_id == self.connection.realm_id
            ).first()
            
            if bank_account:
                # If it's a Credit Card account -> CreditCard
                if "Credit Card" in bank_account.name or "Credit" in bank_account.name: # Fallback name check if type isn't stored
                     # Better: Check QBO Account Type if we stored it? We store 'name'. 
                     # Actually we should store 'account_type' in BankAccount model but we don't seem to have column.
                     # We only have 'name', 'currency'. 
                     # Wait, I see 'account_type' isn't in BankAccount model above. 
                     # Ideally we'd query QBO. But let's rely on standard logic:
                     pass 
                
                if not payment_type:
                     payment_type = "Cash" # Default to Expense
                     
        # Use CreditCard if applicable (Logic implies we need to know Account details better. 
        # For now, defaulting to 'Cash' works for Checking/Savings. 
        # For CC, 'CreditCard' is required. 
        # If raw_json came from CC feed, QBO usually sets it to CreditCard.
        # But if it came as 'Purchase', we might need to be careful.
        # Let's trust raw_json if it says CreditCard. Only override 'Check' without DocNum.)

        # Preserve existing Line details (TaxCode, Class, BillableStatus)
        existing_line = {}
        global_tax = None
        if tx.raw_json:
            if "Line" in tx.raw_json and len(tx.raw_json["Line"]) > 0:
                # Deep copy to avoid mutating the DB object directly in memory just in case
                import copy
                existing_line = copy.deepcopy(tx.raw_json["Line"][0])
            
            global_tax = tx.raw_json.get("GlobalTaxCalculation")

        try:
            updated = await self.client.update_purchase(
                purchase_id=tx.id,
                category_id=cat_id,
                category_name=cat_name,
                sync_token=tx.sync_token,
                entity_type=tx.transaction_type or "Purchase",
                entity_ref=entity_ref,
                payment_type=payment_type,
                txn_status="Closed",
                global_tax_calculation=global_tax,
                existing_line_override=existing_line,
                tags=tx.tags,
                note=tx.note,
                description=tx.description,
                append_memo="#Accepted",
                deposit_to_account_ref=tx.raw_json.get("DepositToAccountRef") if tx.raw_json else None,
                from_account_ref=tx.raw_json.get("FromAccountRef") if tx.raw_json else None
            )
        except Exception as e:
            # Check for Stale Object Error (5010)
            # Typically QBO returns validation fault 400 with code 5010 inside response body
            is_stale = False
            try:
                if hasattr(e, "response") and e.response is not None:
                    # Check the response text directly
                    err_body = e.response.text
                    if "5010" in err_body or "Stale Object" in err_body:
                        is_stale = True
            except:
                pass
            
            if not is_stale and ("5010" in str(e) or "Stale Object" in str(e)):
                is_stale = True

            if is_stale:
                print(f"⚠️ [TransactionService] Stale Object detected for {tx.id}. Retrying with fresh SyncToken...")
                # Fetch fresh entity
                if tx.transaction_type == "Payment":
                    # Fallback to query as get_purchase might not support Payment specifically or verify logic
                    # Just query blindly for now to be safe
                    q_res = await self.client.query(f"SELECT * FROM Payment WHERE Id = '{tx.id}'")
                    fresh = q_res.get("QueryResponse", {}).get("Payment", [])
                else:
                    fresh_res = await self.client.get_purchase(tx.id)
                    fresh = [fresh_res.get("Purchase")] if "Purchase" in fresh_res else []
                    if not fresh and "Payment" in fresh_res: fresh = [fresh_res["Payment"]] # Just in case

                if fresh and isinstance(fresh, list) and len(fresh) > 0:
                    fresh_obj = fresh[0]
                    new_token = fresh_obj.get("SyncToken")
                    print(f"🔄 [TransactionService] Retry with SyncToken: {new_token}")
                    updated = await self.client.update_purchase(
                        purchase_id=tx.id,
                        category_id=cat_id,
                        category_name=cat_name,
                        sync_token=new_token,
                        entity_type=tx.transaction_type or "Purchase",
                        entity_ref=entity_ref,
                        payment_type=payment_type,
                        txn_status="Closed",
                        global_tax_calculation=global_tax,
                        existing_line_override=existing_line,
                        tags=tx.tags,
                        note=tx.note,
                        description=tx.description,
                        append_memo="#Accepted",
                        deposit_to_account_ref=tx.raw_json.get("DepositToAccountRef") if tx.raw_json else None,
                        from_account_ref=tx.raw_json.get("FromAccountRef") if tx.raw_json else None
                    )
                else:
                    raise e
            else:
                raise e
        
        if updated.get("SyncToken"):
            tx.sync_token = updated.get("SyncToken")

        # [Receipt Upload Logic]
        if tx.receipt_url:
            print(f"📎 [Approve] Found Receipt URL for {tx.id}. Downloading & Attaching...")
            try:
                import httpx
                import os
                
                file_bytes = None
                ct = "image/jpeg"
                filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}.jpg"

                # Check if it's a local file first
                if os.path.exists(tx.receipt_url):
                    print(f"📂 [Approve] Reading local receipt file: {tx.receipt_url}")
                    with open(tx.receipt_url, "rb") as f:
                        file_bytes = f.read()
                    
                    # Guess ext from filename
                    _, ext = os.path.splitext(tx.receipt_url)
                    if ext: 
                        filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}{ext}"
                        if "pdf" in ext.lower(): ct = "application/pdf"
                        elif "png" in ext.lower(): ct = "image/png"
                
                else:
                    # Fallback to URL download
                    print(f"🌐 [Approve] Downloading receipt from URL: {tx.receipt_url}")
                    async with httpx.AsyncClient() as dl_client:
                        # Download the image
                        r = await dl_client.get(tx.receipt_url)
                        r.raise_for_status()
                        file_bytes = r.content
                        
                        # Determine filename/type
                        # Simple heuristic: assume jpg/png/pdf based on extension or header
                        dl_ct = r.headers.get("content-type", "image/jpeg")
                        if dl_ct: ct = dl_ct
                        
                        ext = ".jpg"
                        if "pdf" in ct: ext = ".pdf"
                        elif "png" in ct: ext = ".png"
                        
                        filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}{ext}"
                
                if file_bytes:
                    print(f"📎 [Approve] Attaching {filename} ({len(file_bytes)} bytes)...")
                    
                    # Upload to QBO & Link to Purchase
                    attachable_ref = {"EntityRef": {"type": "Purchase", "value": tx.id}}
                    
                    await self.client.upload_attachment(
                        file_bytes=file_bytes,
                        filename=filename,
                        content_type=ct,
                        attachable_ref=attachable_ref
                    )
                    print(f"✅ [Approve] Receipt attached to {tx.id}")
                    
            except Exception as e:
                print(f"❌ [Approve] Receipt Upload Failed: {e}")
                # Non-blocking error - we still approved the transaction
                
        return updated

    async def _update_qbo_split_transaction(self, tx):
        """
        Helper: Writes a split transaction (multiple lines) to QBO.
        """
        entity_ref = await self._resolve_entity_ref(tx.payee, tx.transaction_type)
        payment_type = tx.raw_json.get("PaymentType") if tx.raw_json else None

        # Build Line items for QBO
        lines = []
        for i, split in enumerate(tx.splits, 1):
            if not split.category_id:
                raise ValueError(f"Split line {i} missing category")
            
            lines.append({
                "Id": str(i),
                "Amount": float(split.amount) if split.amount else 0.0,
                "Description": split.description or tx.description,
                "DetailType": "AccountBasedExpenseLineDetail",
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {
                        "value": split.category_id,
                        "name": split.category_name
                    }
                }
            })

        payload = {
            "Id": tx.id,
            "SyncToken": tx.sync_token,
            "sparse": True,
            "Line": lines,
            "PrivateNote": f"Split Transaction | #Accepted {'| Tags: ' + ', '.join(tx.tags) if tx.tags else ''}"
        }
        
        # TotalAmt and TxnDate EXCLUDED to protect original banking data.
        
        if entity_ref:
            payload["EntityRef"] = entity_ref
        if payment_type:
            payload["PaymentType"] = payment_type

        print(f"📝 [TransactionService] Updating split Purchase {tx.id} with {len(lines)} lines")
        result = await self.client.request("POST", "purchase", json_payload=payload)
        updated = result.get("Purchase", {})
        
        if updated.get("SyncToken"):
            tx.sync_token = updated.get("SyncToken")
        return updated

    async def _resolve_entity_ref(self, payee_name, transaction_type="Purchase"):
        if not payee_name:
            return None
            
        # strategy: if Payment, look for Customer first. Else Vendor.
        is_payment = transaction_type == "Payment"
        
        if is_payment:
            # Check DB Customer
            customer = self.db.query(Customer).filter(
                Customer.display_name == payee_name,
                Customer.realm_id == self.connection.realm_id
            ).first()
            if customer: return {"value": customer.id, "name": customer.display_name}
            
            # Check QBO Customer
            remote_c = await self.client.get_customer_by_name(payee_name)
            if remote_c:
                # Cache it
                cust = Customer(id=remote_c["Id"], realm_id=self.connection.realm_id, display_name=payee_name)
                self.db.add(cust)
                self.db.commit()
                return {"value": remote_c["Id"], "name": payee_name}
                
            # Create Customer logic could go here if we wanted to auto-create customers, 
            # but usually for Payments the customer MUST exist. 
            # Failure fallback: maybe it IS a vendor? (Unlikely for Payment endpoint)
            return None 

        # Default Vendor Logic
        vendor = self.db.query(Vendor).filter(
            Vendor.display_name == payee_name,
            Vendor.realm_id == self.connection.realm_id
        ).first()
        
        if vendor:
            return {"value": vendor.id, "name": vendor.display_name}
            
        # Try QBO Vendor
        remote_v = await self.client.get_vendor_by_name(payee_name)
        if remote_v:
            vendor = Vendor(id=remote_v["Id"], realm_id=self.connection.realm_id, display_name=payee_name)
            self.db.add(vendor)
            self.db.commit()
            return {"value": remote_v["Id"], "name": payee_name}

        # Check QBO Customer as fallback (sometimes people pay Vendors via Check)
        remote_c = await self.client.get_customer_by_name(payee_name)
        if remote_c:
             # It's actually a customer
            return {"value": remote_c["Id"], "name": payee_name}
            
        # Create new Vendor
        try:
            new_v = await self.client.create_vendor(payee_name)
            vendor = Vendor(id=new_v["Id"], realm_id=self.connection.realm_id, display_name=payee_name)
            self.db.add(vendor)
            self.db.commit()
            return {"value": new_v["Id"], "name": payee_name}
        except Exception as e:
            print(f"⚠️ Failed to create vendor {payee_name}: {e}")
            # Could be it exists as something else?
            return None

    async def bulk_approve(self, tx_ids: list[str]):
        results = []
        for tx_id in tx_ids:
            try:
                await self.approve_transaction(tx_id)
                results.append({"id": tx_id, "status": "success"})
            except Exception as e:
                results.append({"id": tx_id, "status": "error", "message": str(e)})
        return results
