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
        if not tx.suggested_category_id:
            raise ValueError(f"Transaction {tx.id} missing category")
        
        entity_ref = await self._resolve_entity_ref(tx.payee)
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
                
                # Check raw_json AccountRef type?
                # Use "Cash" (Expense) as safer default for Bank Accounts than "Check"
                # If we force "Cash", it becomes an Expense.
                if payment_type == "Check" and (not tx.raw_json.get("DocNumber")):
                     print(f"🔄 [Approve] Converting 'Check' (no DocNum) to 'Cash' (Expense) for better matching.")
                     payment_type = "Cash"
                elif not payment_type:
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

        updated = await self.client.update_purchase(
            purchase_id=tx.id,
            category_id=tx.suggested_category_id,
            category_name=tx.suggested_category_name,
            sync_token=tx.sync_token,
            entity_ref=entity_ref,
            payment_type=payment_type,
            txn_status="Closed",
            global_tax_calculation=global_tax,
            existing_line_override=existing_line,
            tags=tx.tags,
            amount=float(tx.amount) if tx.amount else 0.0,
            append_memo="#Accepted"
        )
        
        if updated.get("SyncToken"):
            tx.sync_token = updated.get("SyncToken")

        # [Receipt Upload Logic]
        if tx.receipt_url:
            print(f"📎 [Approve] Found Receipt URL for {tx.id}. Downloading & Attaching...")
            try:
                import httpx
                import os
                async with httpx.AsyncClient() as dl_client:
                    # Download the image
                    r = await dl_client.get(tx.receipt_url)
                    r.raise_for_status()
                    file_bytes = r.content
                    
                    # Determine filename/type
                    # Simple heuristic: assume jpg/png/pdf based on extension or header
                    ct = r.headers.get("content-type", "image/jpeg")
                    ext = ".jpg"
                    if "pdf" in ct: ext = ".pdf"
                    elif "png" in ct: ext = ".png"
                    
                    filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}{ext}"
                    
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
        entity_ref = await self._resolve_entity_ref(tx.payee)
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
            "TotalAmt": float(tx.amount) if tx.amount else 0.0,
            "Line": lines,
            "PrivateNote": f"Split Transaction | #Accepted {'| Tags: ' + ', '.join(tx.tags) if tx.tags else ''}"
        }
        
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

    async def _resolve_entity_ref(self, payee_name):
        if not payee_name:
            return None
            
        vendor = self.db.query(Vendor).filter(
            Vendor.display_name == payee_name,
            Vendor.realm_id == self.connection.realm_id
        ).first()
        
        if vendor:
            return {"value": vendor.id, "name": vendor.display_name}
            
        # Try QBO directly
        remote_v = await self.client.get_vendor_by_name(payee_name)
        if remote_v:
            vendor = Vendor(id=remote_v["Id"], realm_id=self.connection.realm_id, display_name=payee_name)
            self.db.add(vendor)
            self.db.commit()
            return {"value": remote_v["Id"], "name": payee_name}
            
        # Create new
        new_v = await self.client.create_vendor(payee_name)
        vendor = Vendor(id=new_v["Id"], realm_id=self.connection.realm_id, display_name=payee_name)
        self.db.add(vendor)
        self.db.commit()
        return {"value": new_v["Id"], "name": payee_name}

    async def bulk_approve(self, tx_ids: list[str]):
        results = []
        for tx_id in tx_ids:
            try:
                await self.approve_transaction(tx_id)
                results.append({"id": tx_id, "status": "success"})
            except Exception as e:
                results.append({"id": tx_id, "status": "error", "message": str(e)})
        return results
