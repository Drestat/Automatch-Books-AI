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
        self.sync_categories()
        self.sync_customers()
        self.sync_bank_accounts()
        # self.sync_tags() # Disabled until we confirm API support
        self.sync_transactions()

    def _get_account_limit(self):
        user = self.db.query(User).filter(User.id == self.connection.user_id).first()
        if not user: return 1 # Default strict
        
        tier = user.subscription_tier.lower()
        if "tier_3" in tier or "enterprise" in tier: return 10
        if "tier_2" in tier or "pro" in tier: return 4
        return 1 # Tier 1 / Free

    async def sync_all(self):
        """Orchestrates the full sync flow."""
        print(f"🚀 [sync_all] Starting for realm_id: {self.connection.realm_id}")
        await self.sync_bank_accounts()
        await self.sync_categories()
        await self.sync_customers()
        await self.sync_vendors()
        await self.sync_transactions()
        print(f"✅ [sync_all] Completed successfully.")

    async def sync_bank_accounts(self):
        print(f"🔄 [sync_bank_accounts] Starting for realm_id: {self.connection.realm_id}")
        
        try:
            # Query for Bank and Credit Card accounts
            query = "SELECT * FROM Account WHERE AccountType IN ('Bank', 'Credit Card')"
            print(f"📝 [sync_bank_accounts] Executing query: {query}")
            
            data = await self.client.query(query)
            print(f"✅ [sync_bank_accounts] Query successful, response: {data}")
            
            accounts = data.get("QueryResponse", {}).get("Account", [])
            print(f"📊 [sync_bank_accounts] Found {len(accounts)} accounts from QBO")
            
            # 1. Mark all existing accounts for this realm as disconnected first
            self.db.query(BankAccount).filter(
                BankAccount.realm_id == self.connection.realm_id
            ).update({BankAccount.is_connected: False})

            # 2. Sync / Reactivate live accounts
            for a in accounts:
                bank = self.db.query(BankAccount).filter(
                    BankAccount.id == a["Id"],
                    BankAccount.realm_id == self.connection.realm_id
                ).first()
                
                if not bank:
                    bank = BankAccount(id=a["Id"], realm_id=self.connection.realm_id)
                    bank.is_active = False  # User must explicitly activate
                
                bank.name = a["Name"]
                bank.currency = a.get("CurrencyRef", {}).get("value", "USD")
                bank.balance = a.get("CurrentBalance", 0)
                bank.is_connected = True # It's in the live list
                
                self.db.add(bank)
                print(f"💾 [sync_bank_accounts] Saved account: {bank.name} (ID: {bank.id})")
                
            self.db.commit()
            print(f"✅ [sync_bank_accounts] Committed {len(accounts)} accounts to database")
            
            self._log("sync", "bank_account", len(accounts), "success", {"synced_metadata": len(accounts)})
        except Exception as e:
            print(f"❌ [sync_bank_accounts] Error: {e}")
            import traceback
            print(f"📋 [sync_bank_accounts] Traceback: {traceback.format_exc()}")
            raise  # Re-raise to let caller handle it

    async def sync_transactions(self):
        # Only sync active accounts
        active_banks = self.db.query(BankAccount).filter(
            BankAccount.realm_id == self.connection.realm_id,
            BankAccount.is_active == True
        ).all()
        
        if not active_banks:
            print("⚠️ No active accounts selected. Skipping transaction sync.")
            return

        self.active_account_ids = [b.id for b in active_banks]
        entity_types = ["Purchase", "Deposit", "CreditCardCredit", "JournalEntry", "Transfer", "BillPayment"]
        
        all_txs = []
        paginated_batch_size = 1000
        
        print(f"🔄 [sync_transactions] Starting full sync for {len(entity_types)} entity types...")
        
        sync_failed = False
        
        for entity in entity_types:
            start_position = 1
            while True:
                # Pagination Loop
                query = f"SELECT * FROM {entity} STARTPOSITION {start_position} MAXRESULTS {paginated_batch_size}"
                
                try:
                    res = await self.client.query(query)
                    batch = res.get("QueryResponse", {}).get(entity, [])
                    
                    if not batch:
                        break
                        
                    all_txs.extend(batch)
                    
                    if len(batch) < paginated_batch_size:
                        break # End of results
                        
                    start_position += len(batch)
                    
                except Exception as e:
                     print(f"⚠️ Error querying {entity} at start_position {start_position}: {e}")
                     try:
                         self.db.rollback()
                     except:
                         pass
                     break # Break inner batch loop to move to next entity
            
            continue
        
        print(f"📊 [sync_transactions] Fetched total of {len(all_txs)} transactions from QBO.")
        
        valid_purchases = []
        synced_qbo_ids = set() 
        
        for p in all_txs:
            qbo_id = p.get("Id")
            if qbo_id:
                synced_qbo_ids.add(str(qbo_id))
        
        for p in all_txs:
            # Skip voided or deleted transactions
            if p.get("TxnStatus") in ["Voided", "Deleted"]:
                continue
            
            # Resolve Account ID (differs by type)
            acc_id = None
            acc_name = "Unknown Account"
            
            if "AccountRef" in p:
                acc_id = str(p["AccountRef"].get("value"))
                acc_name = p["AccountRef"].get("name", "Unknown Account")
            elif "DepositToAccountRef" in p:
                acc_id = str(p["DepositToAccountRef"].get("value"))
                acc_name = p["DepositToAccountRef"].get("name", "Unknown Account")
            elif "FromAccountRef" in p:
                acc_id = str(p["FromAccountRef"].get("value"))
                acc_name = p["FromAccountRef"].get("name", "Unknown Account")
            # BillPayment Handling
            elif "CheckPayment" in p and "BankAccountRef" in p["CheckPayment"]:
                 acc_id = str(p["CheckPayment"]["BankAccountRef"].get("value"))
                 acc_name = p["CheckPayment"]["BankAccountRef"].get("name", "Unknown Account")
            elif "CreditCardPayment" in p and "CCAccountRef" in p["CreditCardPayment"]:
                 acc_id = str(p["CreditCardPayment"]["CCAccountRef"].get("value"))
                 acc_name = p["CreditCardPayment"]["CCAccountRef"].get("name", "Unknown Account")
            
            if not acc_id and "Line" in p:
                for line in p["Line"]:
                    for detail_key in ["JournalEntryLineDetail", "DepositLineDetail", "TransferLineDetail"]:
                        if detail_key in line:
                            detail = line[detail_key]
                            temp_acc_id = str(detail.get("AccountRef", {}).get("value"))
                            if temp_acc_id in self.active_account_ids:
                                acc_id = temp_acc_id
                                acc_name = detail.get("AccountRef", {}).get("name", "Unknown Account")
                                break
                    if acc_id: break

            if not acc_id or acc_id not in self.active_account_ids:
                continue

            valid_purchases.append(p)
            
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
            
            tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
            tx.account_id = acc_id
            tx.account_name = acc_name

            entity_ref = p.get("EntityRef", {})
            vendor_name = entity_ref.get("name")
            if not vendor_name:
                vendor_name = p.get("VendorRef", {}).get("name")
            
            if not vendor_name and "Line" in p:
                for line in p["Line"]:
                    if "DepositLineDetail" in line:
                         entity = line["DepositLineDetail"].get("Entity", {})
                         if entity.get("name"):
                             vendor_name = entity.get("name")
                             break 
                    elif "JournalEntryLineDetail" in line:
                         entity = line["JournalEntryLineDetail"].get("Entity", {})
                         if entity.get("name"):
                             vendor_name = entity.get("name")
                             break
            
            if not vendor_name and "Line" in p and len(p["Line"]) > 0:
                line_desc = p["Line"][0].get("Description")
                if line_desc:
                    vendor_name = line_desc

            tx.description = vendor_name if vendor_name else "Uncategorized Expense"
            tx.amount = p.get("TotalAmt", 0)
            tx.currency = p.get("CurrencyRef", {}).get("value", "USD")
            tx.transaction_type = p.get("PaymentType", "Expense")
            tx.sync_token = p.get("SyncToken")
            tx.note = p.get("PrivateNote")
            
            payee_name = None
            if "EntityRef" in p:
                payee_name = p["EntityRef"].get("name")
            elif "VendorRef" in p:
                payee_name = p["VendorRef"].get("name")
            tx.payee = payee_name
            tx.raw_json = p

            qbo_category_name = None
            qbo_category_id = None
            if "Line" in p:
                for line in p["Line"]:
                    detail = None
                    if "AccountBasedExpenseLineDetail" in line:
                        detail = line["AccountBasedExpenseLineDetail"]
                    elif "JournalEntryLineDetail" in line:
                        detail = line["JournalEntryLineDetail"]
                    elif "DepositLineDetail" in line:
                        detail = line["DepositLineDetail"]
                    elif "SalesItemLineDetail" in line:
                        detail = line["SalesItemLineDetail"]
                    elif "ItemBasedExpenseLineDetail" in line:
                        detail = line["ItemBasedExpenseLineDetail"]
                    
                    if detail:
                        if "AccountRef" in detail:
                            ref_name = detail["AccountRef"].get("name")
                            ref_id = detail["AccountRef"].get("value")
                            if ref_name and "Uncategorized" not in ref_name and str(ref_id) != str(acc_id):
                                qbo_category_name = ref_name
                                qbo_category_id = ref_id
                                break 
                        elif "ItemRef" in detail:
                            qbo_category_name = detail["ItemRef"].get("name")
                            qbo_category_id = detail["ItemRef"].get("value")
                            break
            
            txn_type = None
            purchase_ex = p.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
                        break

            # Categorization Logic
            from app.core.feed_logic import FeedLogic
            is_qbo_matched, decision_reason = FeedLogic.analyze(p)
            tx.is_qbo_matched = is_qbo_matched
            
            if is_qbo_matched:
                if not qbo_category_name and FeedLogic._has_linked_txn(p): 
                     qbo_category_name = "Matched to QBO Entry"

            if txn_type == "54":
                tx.is_bank_feed_import = False
            else:
                tx.is_bank_feed_import = True
            
            # Suggestion Logic
            if qbo_category_name:
                should_overwrite_details = True
                if tx.status in ['pending_approval', 'approved']:
                    should_overwrite_details = False
                
                if should_overwrite_details:
                    tx.status = 'unmatched'
                    tx.suggested_category_name = qbo_category_name
                    tx.suggested_category_id = qbo_category_id
                    tx.confidence = 0.9 
                    tx.reasoning = f"Imported existing { 'link' if 'link' in qbo_category_name.lower() else 'category' } '{qbo_category_name}' from QuickBooks."
            
            self.db.add(tx)
        
        # Pruning
        if synced_qbo_ids and not sync_failed:
            print(f"🧹 [sync_transactions] Pruning stale records. valid_ids_count={len(synced_qbo_ids)}")
            stale_txs = self.db.query(Transaction).filter(
                Transaction.realm_id == self.connection.realm_id,
                Transaction.id.notin_(synced_qbo_ids)
            ).all()
            if stale_txs:
                print(f"Found {len(stale_txs)} stale transactions to delete.")
                for stale in stale_txs:
                    self.db.delete(stale)
            else:
                print("✨ No stale transactions found.")

        self.db.commit()
        self._log("sync", "transaction", len(valid_purchases), "success")

    async def sync_categories(self):
        data = await self.client.query("SELECT * FROM Account WHERE AccountType = 'Expense'")
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

    async def sync_customers(self):
        data = await self.client.query("SELECT * FROM Customer")
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

    async def sync_vendors(self):
        data = await self.client.query("SELECT * FROM Vendor")
        vendors = data.get("QueryResponse", {}).get("Vendor", [])
        for v in vendors:
            vend = self.db.query(Vendor).filter(Vendor.id == v["Id"]).first()
            if not vend:
                vend = Vendor(id=v["Id"], realm_id=self.connection.realm_id)
            vend.display_name = v["DisplayName"]
            self.db.add(vend)
        self.db.commit()
        self._log("sync", "vendor", len(vendors), "success")

    async def approve_transaction(self, tx_id: str):
        """
        Finalizes a transaction and writes it back to QBO.
        - Purchase/Expense: Sparse Update categorization.
        - Bill: Creation of BillPayment to link Bill <-> Bank.
        """
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")

        try:
            # Deep Matching Switch
            # TODO: Add logic to detect if we are matching to a BILL vs CATEGORIZING an expense
            # For now, we assume simple categorization (Purchase Update)
            # If `tx.suggested_category_id` refers to an Account -> Update Purchase
            # If `tx.suggested_category_id` refers to a BILL ID (Logic needed) -> Create BillPayment
            
            # Simple Categorization Flow
            await self._update_qbo_transaction(tx)
            
        except Exception as e:
            print(f"❌ [Approve] Write-Back Failed: {e}")
            raise e

        # Local Update
        tx.status = 'approved' 
        tx.forced_review = False
        tx.is_qbo_matched = True
        self.db.add(tx)
        self.db.commit()
        
        self._log("approve", "transaction", 1, "success", {"tx_id": tx_id})
        return {"status": "success", "message": "Transaction updated in QuickBooks"}

    async def _update_qbo_transaction(self, tx):
        """
        Async Helper: Writes the approved categorization and payee back to QBO.
        """
        print(f"🔄 [Write-Back] Updating QBO Purchase ID {tx.id}...")
        
        if not tx.suggested_category_id or not tx.suggested_category_name:
            raise ValueError(f"Transaction {tx.id} missing category information")
        
        if not tx.sync_token:
            raise ValueError(f"Transaction {tx.id} missing SyncToken")
        
        # 1. Resolve or Create Vendor if Payee changed/assigned
        entity_ref = None
        if tx.payee:
            # Check if this payee name exists as a vendor
            vendor = self.db.query(Vendor).filter(
                Vendor.display_name == tx.payee,
                Vendor.realm_id == self.connection.realm_id
            ).first()
            
            if vendor:
                entity_ref = {"value": vendor.id, "name": vendor.display_name}
            else:
                # 2. Check if Vendor exists in QBO but NOT in local DB
                remote_v = await self.client.get_vendor_by_name(tx.payee)
                if remote_v:
                    print(f"🔗 Linking to existing QBO vendor: {tx.payee}")
                    vendor_id = remote_v.get("Id")
                    entity_ref = {"value": vendor_id, "name": tx.payee}
                    # Save locally for future use
                    vendor = Vendor(
                        id=vendor_id,
                        realm_id=self.connection.realm_id,
                        display_name=tx.payee
                    )
                    self.db.add(vendor)
                    self.db.commit()
                else:
                    # 3. Create NEW vendor in QBO
                    print(f"✨ Creating new vendor: {tx.payee}")
                    new_v_data = await self.client.create_vendor(tx.payee)
                    vendor_id = new_v_data.get("Id")
                    if vendor_id:
                        # Save locally for future use
                        vendor = Vendor(
                            id=vendor_id,
                            realm_id=self.connection.realm_id,
                            display_name=tx.payee
                        )
                        self.db.add(vendor)
                        self.db.commit()
                        entity_ref = {"value": vendor_id, "name": tx.payee}
        
        # Extract PaymentType from original if available (QBO sometimes requires it for updates)
        payment_type = tx.raw_json.get("PaymentType") if tx.raw_json else None

        try:
            updated_purchase = await self.client.update_purchase(
                purchase_id=tx.id,
                category_id=tx.suggested_category_id,
                category_name=tx.suggested_category_name,
                sync_token=tx.sync_token,
                entity_ref=entity_ref,
                payment_type=payment_type
            )
            
            new_sync_token = updated_purchase.get("SyncToken")
            if new_sync_token:
                tx.sync_token = new_sync_token
            
            # Update local payee if QBO returned something different (case normalize)
            res_payee = updated_purchase.get("EntityRef", {}).get("name")
            if res_payee:
                tx.payee = res_payee

            print(f"✅ [Write-Back] Success! QBO Purchase {tx.id} updated")
            return updated_purchase
            
        except Exception as e:
            print(f"❌ [Write-Back] Failed to update QBO Purchase {tx.id}: {e}")
            raise

    async def bulk_approve(self, tx_ids: list[str]):
        """Approves multiple transactions in a batch (Async)"""
        results = []
        for tx_id in tx_ids:
            try:
                await self.approve_transaction(tx_id)
                results.append({"id": tx_id, "status": "success"})
            except Exception as e:
                results.append({"id": tx_id, "status": "error", "message": str(e)})
        
        success_count = len([r for r in results if r["status"] == "success"])
        self._log("bulk_approve", "transaction", success_count, "partial" if success_count < len(tx_ids) else "success", {"results": results})
        return results
