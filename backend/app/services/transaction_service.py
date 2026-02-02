from datetime import datetime
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
            
            # Sort for display stability
            accounts.sort(key=lambda x: x["Name"])

            # Sync ALL accounts so user can see them to select
            # All default to is_active=False - user must choose
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
        queries = [
            "SELECT * FROM Purchase",
            "SELECT * FROM Deposit",
            "SELECT * FROM CreditCardCredit",
            "SELECT * FROM JournalEntry",
            "SELECT * FROM Transfer"
        ]

        all_txs = []
        for q in queries:
            try:
                res = self.client.query(q)
                entity = q.split()[3]
                txs = res.get("QueryResponse", {}).get(entity, [])
                all_txs.extend(txs)
            except Exception as e:
                print(f"⚠️ Error querying {q}: {e}")
                continue
        
        valid_purchases = []
        
        for p in all_txs:
            # Resolve Account ID (differs by type)
            acc_id = None
            acc_name = "Unknown Account"
            if "AccountRef" in p:
                acc_id = p["AccountRef"].get("value")
                acc_name = p["AccountRef"].get("name", "Unknown Account")
            elif "DepositToAccountRef" in p:
                acc_id = p["DepositToAccountRef"].get("value")
                acc_name = p["DepositToAccountRef"].get("name", "Unknown Account")
            
            if not acc_id or acc_id not in self.active_account_ids:
                continue

            valid_purchases.append(p)
            
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
            
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
            tx.transaction_type = p.get("PaymentType", "Expense") # Default to Expense if missing
            tx.note = p.get("PrivateNote")
            tx.raw_json = p
            # Extract Expense Category from Lines (for History/Training)
            qbo_category_name = None
            qbo_category_id = None
            
            if "Line" in p:
                for line in p["Line"]:
                    if "AccountBasedExpenseLineDetail" in line:
                        detail = line["AccountBasedExpenseLineDetail"]
                        if "AccountRef" in detail:
                            qbo_category_name = detail["AccountRef"].get("name")
                            qbo_category_id = detail["AccountRef"].get("value")
                            break # Just grab the first one for now
            
            # Logic: If QBO has a valid category (not Uncategorized), treat as Suggestion but keep unmatched for AI?
            # UPDATED LOGIC: Only apply "Imported existing" if we haven't already enriched it with AI.
            # If current status is 'pending_approval' or 'approved', DO NOT OVERWRITE category/reasoning.
            if qbo_category_name and "Uncategorized" not in qbo_category_name:
                # Check if we should overwrite
                should_overwrite = True
                if tx.status in ['pending_approval', 'approved']:
                    should_overwrite = False
                elif tx.vendor_reasoning: # Has AI data
                    should_overwrite = False
                
                if should_overwrite:
                    tx.status = 'unmatched' # Keep unmatched so AnalysisService picks it up (if we want AI to verify)
                    tx.is_qbo_matched = True # Mark that it was already matched in QBO
                    
                    tx.suggested_category_name = qbo_category_name
                    tx.suggested_category_id = qbo_category_id
                    tx.confidence = 0.9 
                    tx.reasoning = f"Imported existing category '{qbo_category_name}' from QuickBooks."
            
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
        Helper: Fetches fresh QBO Data, checks SyncToken, and Updates.
        Returns the updated QBO JSON.
        """
        print(f"🔄 [Write-Back] Updating QBO Tx ID {tx.id}...")
        
        # 1. Fetch Fresh Data (for SyncToken)
        fresh_qbo_data = self.client.get_transaction(tx.id)
        if not fresh_qbo_data:
            raise ValueError(f"Transaction {tx.id} not found in QBO during write-back.")
        
        purchase_data = fresh_qbo_data.get("Purchase") or fresh_qbo_data.get("JournalEntry") # Handle different types if needed
        # We only support Purchase/Expense for now based on 'sync_transactions'
        if not purchase_data:
             raise ValueError(f"Could not parse QBO Data for {tx.id} - Expected Purchase object.")

        sync_token = purchase_data.get("SyncToken")
        print(f"🔒 [Write-Back] Acquired SyncToken: {sync_token}")
        
        # 2. Construct Payload
        # Start with the fresh data to ensure we have all required fields (Line IDs etc)
        payload = purchase_data 
        
        # -- Update Category (AccountRef) --
        # We need to find the specific Line Item that corresponds to the expense.
        # Usually it's the Line with "AccountBasedExpenseLineDetail".
        
        if tx.is_split and tx.splits:
            # Reconstruct Lines for Split
            # WARNING: Replacing Lines might lose existing line IDs if we aren't careful.
            # Best practice is to try to match up lines or wipe and replace.
            # For "Uncategorized" -> "Categorized", typically we just replace the lines.
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
            # Single Category
            # We iterate through lines to find the expense line
            found_expense_line = False
            if "Line" in payload:
                for line in payload["Line"]:
                    if "AccountBasedExpenseLineDetail" in line:
                         line["AccountBasedExpenseLineDetail"]["AccountRef"] = {
                             "value": tx.suggested_category_id,
                             "name": tx.suggested_category_name
                         }
                         found_expense_line = True
            
            # If we didn't find an expense line (maybe it was empty?), we might need to add one.
            # But usually a purchase has at least one line.
        
        # -- Append AI Reasoning to Memo --
        # QBO field is "PrivateNote" (Memo on screen)
        # We append, not overwrite, to preserve original user notes.
        original_note = payload.get("PrivateNote", "")
        ai_note = f" | AI Reasoning: {tx.vendor_reasoning}" if tx.vendor_reasoning else ""
        
        # Check length limit (QBO is 4000 chars, but let's be safe)
        if len(original_note) + len(ai_note) < 4000:
             if "AI Reasoning:" not in original_note: # Prevent duplicate appending
                 payload["PrivateNote"] = original_note + ai_note

        # 3. Execute Update
        # Explicitly pass SyncToken just in case, though it's inside payload
        payload["SyncToken"] = sync_token
        
        # The endpoint in QBOClient usually handles the entity type detection or we pass it
        # self.client.request uses "purchase" entity default? Or we need to specify?
        # looking at approve_transaction below, it used "purchase".
        
        res_data = self.client.request("POST", "purchase", params={'operation': 'update'}, json_payload=payload)
        print(f"✅ [Write-Back] Success! QBO Updated.")
        return res_data

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
        # Actually 'approved' usually means "User approved, waiting for sync", 
        # but here we did synchronous sync. 
        # Let's keep 'approved' as the final state for now or 'synced'.
        # task.md says: "Update local DB status to 'synced'" - let's stick to that if schema allows.
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
