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
            "free_user": 1,
            "personal": 2,
            "business": 100,
            "corporate": 1000,
            # Legacy keys
            "starter": 1,
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

    async def approve_transaction(self, tx_id: str, optimistic: bool = True):
        """
        Finalizes a transaction locally. 
        If optimistic=True, returns immediately after marking status as 'pending_qbo'.
        If optimistic=False, runs synchronously (legacy/testing).
        """
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")
        
        # Local state update
        tx.status = 'pending_qbo' # Trigger for Worker
        tx.forced_review = False
        self.db.add(tx)
        self.db.commit()

        if not optimistic:
            print(f"🔄 [Approve] Synchronous approval requested for {tx_id}")
            return await self.sync_approved_to_qbo(tx_id)

        print(f"🚀 [Approve] Transaction {tx_id} marked as 'pending_qbo'. Returning optimistically.")
        return {"status": "success", "message": "Transaction queued for approval", "tx_id": tx_id}

    async def sync_approved_to_qbo(self, tx_id: str):
        """
        Backgroundable method to actually push an approved transaction to QBO.
        """
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx or tx.status != 'pending_qbo':
            print(f"⚠️ [SyncToQBO] Transaction {tx_id} not found or not in pending state.")
            return

        try:
            if tx.is_split and tx.splits:
                print(f"✂️ [SyncToQBO] Processing SPLIT transaction {tx.id}...")
                await self._update_qbo_split_transaction(tx)
            else:
                print(f"🏷️ [SyncToQBO] Processing standard transaction {tx.id}...")
                await self._update_qbo_transaction(tx)
            
            # Post-Process: Upload Receipt (if any)
            await self._upload_receipt(tx)
            
            # Cleanup amount if was 0
            if not tx.amount or tx.amount == 0:
                try:
                    qbo_tx = await self.client.get_purchase(tx.id)
                    purchase_data = qbo_tx.get("Purchase", {})
                    real_amount = purchase_data.get("TotalAmt")
                    if real_amount:
                        tx.amount = real_amount
                except Exception as e:
                    print(f"⚠️ [SyncToQBO] Failed to fetch amount: {e}")

            # Final success state
            tx.status = 'approved'
            tx.is_qbo_matched = True
            self.db.add(tx)
            self.db.commit()
            
            self._log("approve", "transaction", 1, "success", {"tx_id": tx_id, "is_split": tx.is_split})
            
            # [Gamification] Award XP for Categorization
            try:
                from app.services.gamification_service import GamificationService
                gs = GamificationService(self.db)
                # "categorize" action yields 10 XP
                xp_result = gs.add_xp(self.connection.user_id, "categorize", {"tx_id": tx_id})
                print(f"🎮 [Gamification] {self.connection.user_id} gained XP: {xp_result}")
            except Exception as gx:
                print(f"⚠️ [Gamification] Failed to award XP: {gx}")

            return {"status": "success", "message": "Transaction synchronized with QuickBooks", "xp_earned": 10}


        except Exception as e:
            print(f"❌ [SyncToQBO] Write-Back Failed: {e}")
            tx.status = 'error_qbo'
            tx.reasoning = f"QBO Sync Failed: {str(e)}"
            self.db.add(tx)
            self.db.commit()
            self._log("approve", "transaction", 1, "error", {"tx_id": tx_id, "error": str(e)})
            raise e

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
        if not payment_type or payment_type == "Check": 
            # Note: Even if it says "Check" in raw_json, if it has no DocNum, it might be a mis-classification 
            # or default QBO behavior. We prefer "Cash" (Expense) for matching unless user explicitly intends a Check.
            
            # Fetch Account Type
            bank_account = self.db.query(BankAccount).filter(
                BankAccount.id == tx.account_id,
                BankAccount.realm_id == self.connection.realm_id
            ).first()
            
            if bank_account:
                if "Credit Card" in bank_account.name or "Credit" in bank_account.name: 
                     pass 
                
                if not payment_type:
                     payment_type = "Cash" # Default to Expense

        # Preserve existing Line details
        existing_line = {}
        global_tax = None
        if tx.raw_json:
            if "Line" in tx.raw_json and len(tx.raw_json["Line"]) > 0:
                import copy
                existing_line = copy.deepcopy(tx.raw_json["Line"][0])
            global_tax = tx.raw_json.get("GlobalTaxCalculation")

        # HANDLE PAYMENT/BILLPAYMENT CATEGORY IGNORE
        # QBOClient intentionally ignores AccountRef for these types to preserve Invoice/Bill links.
        # We must document the user's intent in the Memo.
        append_memo = "#Accepted"
        if tx.transaction_type in ["Payment", "BillPayment"] and cat_name:
            print(f"⚠️ [Approve] Transaction {tx.id} is {tx.transaction_type}. Category '{cat_name}' will be noted in Memo (not applied to GL).")
            append_memo = f"#Accepted | [App Category: {cat_name}]"

        try:
            # NEW OPTIMIZATION: If the transaction already exists in QBO (has SyncToken)
            # and the user hasn't explicitly overridden the category, we skip the Line update.
            # This handles:
            # - Transactions already matched (is_qbo_matched=True)
            # - Transactions with match suggestions (confidence > 0.8)
            # - Any existing ledger item where we are just adding a memo/stamp.
            skip_line_update = False
            if tx.sync_token and not tx.category_id:
                print(f"🛡️ [Approve] Skipping line update for existing transaction {tx.id} to preserve original ledger structure.")
                skip_line_update = True

            updated = await self.client.update_purchase(
                purchase_id=tx.id,
                category_id=cat_id if not skip_line_update else None,
                category_name=cat_name if not skip_line_update else None,
                sync_token=tx.sync_token,
                entity_type=tx.transaction_type or "Purchase",
                entity_ref=entity_ref,
                payment_type=payment_type,
                txn_status="Closed",
                global_tax_calculation=global_tax,
                existing_line_override=existing_line if not skip_line_update else None,
                tags=tx.tags,
                note=tx.note,
                description=tx.description,
                append_memo=append_memo,
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
                # Fetch fresh entity using the specific type
                fresh_res = await self.client.get_entity(tx.id, tx.transaction_type or "Purchase")
                
                # Extract object from wrapper (QBO returns { "Purchase": { ... } })
                # But sometimes it's flattened or has a different key.
                entity_key = tx.transaction_type or "Purchase"
                if tx.transaction_type == "Expense": entity_key = "Purchase" # QBO mapping
                
                fresh_obj = fresh_res.get(entity_key)
                if not fresh_obj:
                    # Try to find any key that might be the object
                    for k, v in fresh_res.items():
                        if isinstance(v, dict) and "SyncToken" in v:
                            fresh_obj = v
                            break

                if fresh_obj:
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
                        append_memo=append_memo,
                        deposit_to_account_ref=tx.raw_json.get("DepositToAccountRef") if tx.raw_json else None,
                        from_account_ref=tx.raw_json.get("FromAccountRef") if tx.raw_json else None
                    )
                else:
                    raise e
            else:
                # GUARDIAN LOGIC: Handle Object Not Found (610) / Deleted / Voided
                # If QBO says "Object Not Found", it means the ID changed or was deleted.
                # We attempt to find a replacement by Amount + Approximate Date.
                is_not_found = False
                try:
                    if hasattr(e, "response") and e.response is not None:
                        err_body = e.response.text
                        if "Object Not Found" in err_body or "610" in err_body:
                            is_not_found = True
                except:
                    pass

                if is_not_found:
                    print(f"🛡️ [Guardian] Transaction {tx.id} is GHOSTED in QBO (Object Not Found). Hunting for replacement...")
                    
                    # 1. Search for replacement in QBO
                    # Range: +/- 3 days? Or just match Amount exactly?
                    # Let's try exact Amount for now since date might shift slightly on posting.
                    query = f"select * from Purchase where TotalAmt = '{tx.amount}'"
                    result = await self.client.query(query)
                    candidates = result.get("QueryResponse", {}).get("Purchase", [])
                    
                    # Filter candidates by Date (strict +/- 4 days)
                    from datetime import timedelta
                    target_date = tx.date.date()
                    found_replacement = None
                    
                    for cand in candidates:
                        # Parse QBO date (YYYY-MM-DD)
                        # Minimal parsing
                        c_date_str = cand.get("TxnDate")
                        if not c_date_str: continue
                        
                        y, m, d = map(int, c_date_str.split('-'))
                        c_date = datetime(y, m, d).date()
                        
                        diff = abs((c_date - target_date).days)
                        if diff <= 4:
                            found_replacement = cand
                            break

                    if found_replacement:
                        new_id = found_replacement["Id"]
                        print(f"✅ [Guardian] Found Replacement: {new_id} (Date: {found_replacement['TxnDate']}). Heal/Swizzle...")
                        
                        # DELETE any existing local transaction that might have the new ID (to avoid PK collision)
                        existing_new = self.db.query(Transaction).filter(
                            Transaction.id == new_id, 
                            Transaction.realm_id == self.connection.realm_id
                        ).first()
                        
                        if existing_new:
                            print(f"🗑️ [Guardian] Deleting collision record {new_id} to make way for swap.")
                            # We might want to migrate splits from existing_new? 
                            # Usually existing_new is just a raw feed item, so safe to nuke.
                            self.db.delete(existing_new)
                            self.db.commit()

                        # Heal the current transaction (update PK)
                        # Direct SQL update to avoid ORM complexity with PKs
                        from sqlalchemy import text
                        self.db.execute(
                            text("UPDATE transactions SET id = :new_id, sync_token = :new_token WHERE id = :old_id"),
                            {"new_id": new_id, "new_token": found_replacement.get("SyncToken"), "old_id": tx.id}
                        )
                        # Also update splits
                        self.db.execute(
                             text("UPDATE transaction_splits SET transaction_id = :new_id WHERE transaction_id = :old_id"),
                             {"new_id": new_id, "old_id": tx.id}
                        )
                        self.db.commit()
                        
                        # Update object in memory
                        tx.id = new_id
                        tx.sync_token = found_replacement.get("SyncToken")
                        
                        print(f"🔄 [Guardian] Retry update with NEW ID: {tx.id}")
                        
                        # Recursive retry
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
                            append_memo=append_memo,
                            deposit_to_account_ref=tx.raw_json.get("DepositToAccountRef") if tx.raw_json else None,
                            from_account_ref=tx.raw_json.get("FromAccountRef") if tx.raw_json else None
                        )
                    else:
                        print(f"❌ [Guardian] No replacement found. Transaction is truly lost.")
                        raise e
                else:
                    raise e
        
        if updated.get("SyncToken"):
            tx.sync_token = updated.get("SyncToken")

        # R6: Note: Receipt upload moved to parent approve_transaction to avoid redundancy

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
            
        # strategy: if Customer-facing type, look for Customer first. Else Vendor.
        is_customer_type = transaction_type in ["Payment", "SalesReceipt", "RefundReceipt", "CreditMemo"]
        
        if is_customer_type:
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

    def _map_to_qbo_attachable_type(self, transaction_type: str) -> str:
        """
        Maps internal transaction types to valid QBO Attachable EntityRef types.
        QBO API requires specific entity types for AttachableRef.

        Ref: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/attachable
        """
        type_mapping = {
            "Purchase": "Purchase",
            "Check": "Purchase",      # QBO API uses 'Purchase' for Checks/Expenses
            "CreditCard": "Purchase", 
            "Expense": "Purchase",    # QBO API uses 'Purchase' for Expenses
            "Bill": "Bill",
            "BillPayment": "BillPayment",
            "Payment": "Payment",
            "Deposit": "Deposit",
            "JournalEntry": "JournalEntry",
            "Invoice": "Invoice",
            "SalesReceipt": "SalesReceipt",
            "RefundReceipt": "RefundReceipt",
            "CreditMemo": "CreditMemo"
        }

        # Return mapped type or fallback to Purchase (most common)
        mapped_type = type_mapping.get(transaction_type, "Purchase")

        if mapped_type != transaction_type:
            print(f"🔄 [Attachable] Mapped transaction type '{transaction_type}' -> '{mapped_type}' for QBO API")

        return mapped_type

    async def _upload_receipt(self, tx):
        """
        Uploads an associated receipt to QBO.
        Prefers binary content from DB (serverless-safe), fallbacks to local file or URL download.
        Correctly detects content-type and filename from URL extension.
        """
        if not tx.receipt_url and not tx.receipt_content:
            return

        print(f"📎 [Approve] Found Receipt for {tx.id}. Preparing attachment...")
        try:
            import httpx
            import os
            from urllib.parse import urlparse

            file_bytes = None
            ct = "image/jpeg"
            ext = ".jpg"

            # 0. Pre-detect extension and content-type from URL path
            if tx.receipt_url:
                parsed_url = urlparse(tx.receipt_url)
                _, url_ext = os.path.splitext(parsed_url.path)
                if url_ext:
                    url_ext = url_ext.lower()
                    ext = url_ext
                    if url_ext == ".pdf": ct = "application/pdf"
                    elif url_ext == ".png": ct = "image/png"
                    elif url_ext in [".jpg", ".jpeg"]: ct = "image/jpeg"

            filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}{ext}"

            # 1. Prefer Binary Persistence (Serverless-Safe)
            if tx.receipt_content:
                print(f"📦 [Approve] Using binary receipt content from DB for {tx.id}")
                file_bytes = tx.receipt_content

            # 2. Check local file (Local Dev / Single instance)
            elif tx.receipt_url and os.path.exists(tx.receipt_url):
                print(f"📂 [Approve] Reading local receipt file: {tx.receipt_url}")
                with open(tx.receipt_url, "rb") as f:
                    file_bytes = f.read()

            # 3. Fallback to URL download (External Storage)
            elif tx.receipt_url and tx.receipt_url.startswith("http"):
                print(f"🌐 [Approve] Downloading receipt from URL: {tx.receipt_url}")
                async with httpx.AsyncClient() as dl_client:
                    r = await dl_client.get(tx.receipt_url)
                    r.raise_for_status()
                    file_bytes = r.content

                    dl_ct = r.headers.get("content-type")
                    if dl_ct: 
                        ct = dl_ct
                        # Adjust filename if download provides better type info
                        if "pdf" in ct: ext = ".pdf"
                        elif "png" in ct: ext = ".png"
                        elif "jpeg" in ct: ext = ".jpg"
                        filename = f"Receipt-{tx.date.strftime('%Y-%m-%d')}-{tx.id[:8]}{ext}"

            if file_bytes:
                print(f"📎 [Approve] Attaching {filename} ({len(file_bytes)} bytes)...")

                # Map transaction type to valid QBO Attachable entity type
                qbo_entity_type = self._map_to_qbo_attachable_type(tx.transaction_type or "Purchase")

                attachable_ref = {
                    "EntityRef": {"type": qbo_entity_type, "value": tx.id},
                    "IncludeOnSend": True
                }

                await self.client.upload_attachment(
                    file_bytes=file_bytes,
                    filename=filename,
                    content_type=ct,
                    attachable_ref=attachable_ref
                )
                print(f"✅ [Approve] Receipt attached to {tx.id} as {qbo_entity_type}")

        except Exception as e:
            print(f"❌ [Approve] Receipt Upload Failed: {e}")
            # Non-blocking error
