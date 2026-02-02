from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.qbo import Transaction, QBOConnection, Category, Customer, SyncLog, TransactionSplit, BankAccount, Tag
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

    def sync_bank_accounts(self):
        print(f"🔄 [sync_bank_accounts] Starting for realm_id: {self.connection.realm_id}")
        
        try:
            # Query for Bank and Credit Card accounts
            query = "SELECT * FROM Account WHERE AccountType IN ('Bank', 'Credit Card')"
            print(f"📝 [sync_bank_accounts] Executing query: {query}")
            
            data = self.client.query(query)
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

    def sync_transactions(self):
        # Only sync active accounts
        active_banks = self.db.query(BankAccount).filter(
            BankAccount.realm_id == self.connection.realm_id,
            BankAccount.is_active == True
        ).all()
        
        if not active_banks:
            print("⚠️ No active accounts selected. Skipping transaction sync.")
            return

        self.active_account_ids = [b.id for b in active_banks]

        # Fetch from multiple sources: Purchase, Deposit, CreditCardCredit, JournalEntry, Transfer
        # Fetch from multiple sources: Purchase, Deposit, CreditCardCredit, JournalEntry, Transfer
        # We must sync EVERYTHING to safely prune deleted items.
        entity_types = ["Purchase", "Deposit", "CreditCardCredit", "JournalEntry", "Transfer"]
        
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
                    res = self.client.query(query)
                    batch = res.get("QueryResponse", {}).get(entity, [])
                    
                    if not batch:
                        break
                        
                    all_txs.extend(batch)
                    
                    if len(batch) < paginated_batch_size:
                        break # End of results
                        
                    start_position += len(batch)
                    
                except Exception as e:
                     print(f"⚠️ Error querying {entity} at start_position {start_position}: {e}")
                     sync_failed = True
                     break
            
            if sync_failed:
                break
        
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
            
            # Special case for JournalEntry and Transfer where the account might be in the lines
            if not acc_id and "Line" in p:
                for line in p["Line"]:
                    # Look for the primary bank account in the lines if not set in header
                    # Usually for Transfers/JournalEntries, we care if ONE of the lines matches our active account
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
            
            # ============================================================================
            # NO FILTER: Sync ALL transactions for data integrity.
            # Filtering is handled by the "View Status" logic in the frontend.
            # ============================================================================
            
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
                # For new transactions, is_excluded defaults to False.
                # For existing transactions, is_excluded is preserved by not being overwritten.
            
            tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
            
            # Map Account (Source)
            tx.account_id = acc_id
            tx.account_name = acc_name

            # Map Description (Vendor + Memo)
            entity_ref = p.get("EntityRef", {})
            vendor_name = entity_ref.get("name")
            memo = p.get("PrivateNote") # QBO 'Memo' is often in PrivateNote or Line items
            
            # Construct a rich description for AI
            desc_parts = []
            if vendor_name:
                desc_parts.append(vendor_name)
            if memo:
                 desc_parts.append(memo)
            
            # Fallback to Line description if main description is empty
            if not desc_parts and "Line" in p and len(p["Line"]) > 0:
                line_desc = p["Line"][0].get("Description")
                if line_desc:
                    desc_parts.append(line_desc)

            tx.description = " - ".join(desc_parts) if desc_parts else "Uncategorized Expense"

            tx.amount = p.get("TotalAmt", 0)
            tx.currency = p.get("CurrencyRef", {}).get("value", "USD")
            tx.transaction_type = p.get("PaymentType", "Expense")
            
            # Store SyncToken for future updates
            tx.sync_token = p.get("SyncToken") # Default to Expense if missing
            tx.note = p.get("PrivateNote")
            tx.raw_json = p
            # Extract Expense Category from Lines (for History/Training)
            qbo_category_name = None
            qbo_category_id = None
            if "Line" in p:
                has_linked_txn = False
                for line in p["Line"]:
                    # 1. Check for Linked Transactions (Highest priority for 'matched' status)
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        has_linked_txn = True
                        # If we find a linked txn, we can consider it matched
                        # But we still continue to look for a specific category name
                    
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
                # EXTRACT Transaction Type and Metadata
                txn_type = None
                doc_number = p.get("DocNumber")
                private_note = p.get("PrivateNote")
                entity_ref = p.get("EntityRef")
                metadata = p.get("MetaData", {})
                create_time_str = metadata.get("CreateTime", "")
                
                # Check if created today (within last 24h of sync)
                is_created_today = False
                if create_time_str:
                    try:
                        create_dt = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        # Relaxed today check: same calendar day or < 24h
                        if (now - create_dt).total_seconds() < 86400:
                            is_created_today = True
                    except: pass

                purchase_ex = p.get("PurchaseEx", {})
                if "any" in purchase_ex:
                    for item in purchase_ex["any"]:
                        if item.get("value", {}).get("Name") == "TxnType":
                            txn_type = item.get("value", {}).get("Value")
                            break


                # Check if the category is specific (not generic "Uncategorized")
                is_specific_category = False
                if qbo_category_name:
                    cat_lower = qbo_category_name.lower()
                    if "uncategorized" not in cat_lower and "ask my accountant" not in cat_lower:
                        is_specific_category = True
                
                
                # CATEGORIZED vs FOR REVIEW DISCRIMINATOR:
                # A transaction is "Categorized" if:
                # 1. It has a specific category (not "Uncategorized" or "Ask My Accountant")
                #    - This includes manual entries created with a category
                #    - This includes bank feed transactions matched to a category
                # 2. OR it has an explicit link (LinkedTxn) from QBO matching
                # 3. OR it was just "Added" (Created Today)
                
                # If it has a specific category, it's categorized (respects existing QBO categories)
                if is_specific_category:
                    tx.is_qbo_matched = True
                    if not qbo_category_name:
                        qbo_category_name = "Matched to QBO Entry"
                else:
                    # No specific category = For Review
                    tx.is_qbo_matched = False
                
                # BANK FEED vs MANUAL ENTRY DISCRIMINATOR:
                # TxnType=54 indicates a manual entry (not from bank feed)
                # QBO Banking UI hides these from the Banking tab
                if txn_type == "54":
                    tx.is_bank_feed_import = False
                else:
                    tx.is_bank_feed_import = True
                
                # IMPORTANT: If we found a category, we ALWAYS want it as the suggestion
                if qbo_category_name:
                    # Check if we should overwrite the categorization details
                    should_overwrite_details = True
                    if tx.status in ['pending_approval', 'approved']:
                        should_overwrite_details = False
                    elif tx.vendor_reasoning: # Has AI data, don't overwrite its reasoning
                        should_overwrite_details = False
                    
                    if should_overwrite_details:
                        tx.status = 'unmatched' # Keep unmatched so AnalysisService picks it up
                        tx.suggested_category_name = qbo_category_name
                        tx.suggested_category_id = qbo_category_id
                        tx.confidence = 0.9 
                        tx.reasoning = f"Imported existing { 'link' if 'link' in qbo_category_name.lower() else 'category' } '{qbo_category_name}' from QuickBooks."
            
            # --- Smart Tagging Logic (Historical) ---
            # Try to find a recent approved transaction with same Vendor/Description to copy tags
            if not tx.tags:
                historical_tx_query = self.db.query(Transaction).filter(
                    Transaction.realm_id == self.connection.realm_id,
                    Transaction.status == 'approved',
                )
                
                # Filter by description or vendor name match
                # Using simple description match for now as 'vendor_name' is derived
                match_desc = vendor_name if vendor_name else tx.description
                # We need to match somewhat loosely or strictly? Let's try strict description match first
                # or strict vendor match if available.
                
                # Ideally we check: if we found a vendor name, match other txs with that vendor.
                # But 'vendor_name' isn't a column on Transaction (it's embedded or looked up).
                # So we match on description.
                historical_tx_query = historical_tx_query.filter(Transaction.description == tx.description)
                
                # Ensure it has tags
                # JSON/Array check in SQL Alchemy can be tricky depending on backend, 
                # but checking for non-empty list in python after fetch is safer if volume is low,
                # or using proper JSON operators. 
                # For simplicity/compatibility, let's just order by date and check in python.
                historical_tx_query = historical_tx_query.order_by(Transaction.date.desc())
                
                candidate = historical_tx_query.first()
                if candidate and candidate.tags:
                    tx.tags = candidate.tags
                    # If we auto-tagged, append to reasoning
                    tx.reasoning = (tx.reasoning or "") + " [Auto-Tagged from History]"

            self.db.add(tx)
        
        # ============================================================================
        # PRUNING: Delete transactions that no longer exist in QBO
        # (or were moved to a type we don't sync, safely removing them)
        # ============================================================================
        if synced_qbo_ids and not sync_failed:
            # Only prune if we successfully fetched at least 1 item to avoid accidental wipe on error
            print(f"🧹 [sync_transactions] Pruning stale records. valid_ids_count={len(synced_qbo_ids)}")
            
            # Find ghosts
            stale_txs = self.db.query(Transaction).filter(
                Transaction.realm_id == self.connection.realm_id,
                Transaction.id.notin_(synced_qbo_ids)
            ).all()
            
            if stale_txs:
                print(f"Found {len(stale_txs)} stale transactions to delete.")
                for stale in stale_txs:
                    print(f"❌ Deleting Stale Transaction: {stale.description} (ID: {stale.id})")
                    self.db.delete(stale)
            else:
                print("✨ No stale transactions found.")

        self.db.commit()
        self._log("sync", "transaction", len(valid_purchases), "success")

    def sync_categories(self):
        data = self.client.query("SELECT * FROM Account WHERE AccountType = 'Expense'")
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
        data = self.client.query("SELECT * FROM Customer")
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

    def approve_transaction(self, tx_id: str):
        """Finalizes a transaction and writes it back to QBO"""
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")

    def _update_qbo_transaction(self, tx):
        """
        Helper: Writes the approved categorization back to QBO.
        Sets the category and marks as manually categorized (TxnType=54).
        """
        print(f"🔄 [Write-Back] Updating QBO Purchase ID {tx.id}...")
        
        # Validate we have the required data
        if not tx.suggested_category_id or not tx.suggested_category_name:
            raise ValueError(f"Transaction {tx.id} missing category information")
        
        if not tx.sync_token:
            raise ValueError(f"Transaction {tx.id} missing SyncToken")
        
        # Handle split transactions
        if tx.is_split and tx.splits:
            # For split transactions, we need to use the complex update
            # This is a future enhancement - for now, we'll raise an error
            raise NotImplementedError("Split transaction write-back not yet implemented")
        
        # Use the new update_purchase method from QBOClient
        try:
            updated_purchase = self.client.update_purchase(
                purchase_id=tx.id,  # Transaction.id is the QBO Purchase ID
                category_id=tx.suggested_category_id,
                category_name=tx.suggested_category_name,
                sync_token=tx.sync_token
            )
            
            # Update the SyncToken in our database for future updates
            new_sync_token = updated_purchase.get("SyncToken")
            if new_sync_token:
                tx.sync_token = new_sync_token
            
            print(f"✅ [Write-Back] Success! QBO Purchase {tx.id} updated")
            return updated_purchase
            
        except Exception as e:
            print(f"❌ [Write-Back] Failed to update QBO Purchase {tx.id}: {e}")
            raise

    def approve_transaction(self, tx_id: str):
        """Finalizes a transaction and writes it back to QBO"""
        tx = self.db.query(Transaction).filter(
            Transaction.id == tx_id,
            Transaction.realm_id == self.connection.realm_id
        ).first()

        if not tx:
            raise ValueError(f"Transaction {tx_id} not found")

        # Perform the Real Write-Back
        try:
            self._update_qbo_transaction(tx)
        except Exception as e:
            print(f"❌ [Approve] Write-Back Failed: {e}")
            raise e # Fail the approval if QBO write fails (Data Integrity)

        # Update Mirror Status to 'synced' to indicate full round-trip
        tx.status = 'approved' 
        tx.forced_review = False # Reset forced review flag
        # Checking models... Status enum usually: unmatched, pending_approval, approved.
        # I'll stick to 'approved' to avoid Enum errors unless I verify 'synced' exists.
        
        self.db.add(tx)
        self.db.commit()
        
        self._log("approve", "transaction", 1, "success", {"tx_id": tx_id})
        return {"status": "success", "message": "Transaction updated in QuickBooks"}

    def bulk_approve(self, tx_ids: list[str]):
        """Approves multiple transactions in a batch"""
        results = []
        for tx_id in tx_ids:
            try:
                self.approve_transaction(tx_id)
                results.append({"id": tx_id, "status": "success"})
            except Exception as e:
                results.append({"id": tx_id, "status": "error", "message": str(e)})
        
        success_count = len([r for r in results if r["status"] == "success"])
        self._log("bulk_approve", "transaction", success_count, "partial" if success_count < len(tx_ids) else "success", {"results": results})
        return results
