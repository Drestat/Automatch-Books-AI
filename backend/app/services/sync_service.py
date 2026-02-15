from datetime import datetime
from sqlalchemy.orm import Session
from app.models.qbo import Transaction, QBOConnection, Category, Customer, Vendor, SyncLog, BankAccount
from app.models.user import User
from app.services.qbo_client import QBOClient
from app.core.feed_logic import FeedLogic

class SyncService:
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

    async def sync_all(self):
        """Orchestrates the full sync flow."""
        print(f"🚀 [SyncService] Starting sync for realm: {self.connection.realm_id}")
        await self.sync_bank_accounts()
        await self.sync_categories()
        await self.sync_customers()
        await self.sync_vendors()
        await self.sync_transactions()
        print(f"✅ [SyncService] Completed sync for realm: {self.connection.realm_id}")

    async def sync_bank_accounts(self):
        print(f"🔄 [SyncService] Syncing bank accounts...")
        try:
            query = "SELECT * FROM Account WHERE AccountType IN ('Bank', 'Credit Card')"
            data = await self.client.query(query)
            accounts = data.get("QueryResponse", {}).get("Account", [])
            
            self.db.query(BankAccount).filter(
                BankAccount.realm_id == self.connection.realm_id
            ).update({BankAccount.is_connected: False})

            for a in accounts:
                bank = self.db.query(BankAccount).filter(
                    BankAccount.id == a["Id"],
                    BankAccount.realm_id == self.connection.realm_id
                ).first()
                
                if not bank:
                    bank = BankAccount(id=a["Id"], realm_id=self.connection.realm_id)
                    bank.is_active = False
                
                bank.name = a["Name"]
                bank.currency = a.get("CurrencyRef", {}).get("value", "USD")
                bank.balance = a.get("CurrentBalance", 0)
                bank.is_connected = True
                self.db.add(bank)
                
            self.db.commit()
            self._log("sync", "bank_account", len(accounts), "success")
        except Exception as e:
            print(f"❌ [SyncService] Bank account sync failed: {e}")
            raise

    async def sync_transactions(self):
        active_banks = self.db.query(BankAccount).filter(
            BankAccount.realm_id == self.connection.realm_id,
            BankAccount.is_active == True
        ).all()
        
        if not active_banks:
            print("⚠️ No active accounts. Skipping tx sync.")
            return

        active_account_ids = [b.id for b in active_banks]
        entity_types = [
            "Purchase", "Deposit", "JournalEntry", 
            "Transfer", "BillPayment", "Payment", "SalesReceipt", 
            "RefundReceipt", "CreditMemo"
        ]
        
        all_txs = []
        
        # Date Filter: Last 365 Days (and future)
        from datetime import timedelta, date
        start_date = (date.today() - timedelta(days=365)).isoformat()
        
        print(f"🔄 [SyncService] Fetching history since {start_date}...")
        
        batch_size = 1000
        
        for entity in entity_types:
            start_pos = 1
            while True:
                # Add 'TxnDate' filter
                query = f"SELECT * FROM {entity} WHERE TxnDate >= '{start_date}' STARTPOSITION {start_pos} MAXRESULTS {batch_size}"
                try:
                    res = await self.client.query(query)
                    batch = res.get("QueryResponse", {}).get(entity, [])
                    
                    if not batch: break
                    
                    # Tag with source entity
                    for item in batch:
                        item["_source_entity"] = entity
                    
                    all_txs.extend(batch)
                    
                    if len(batch) < batch_size: break
                    start_pos += len(batch)
                    
                except Exception as e:
                    print(f"⚠️ Error syncing {entity}: {e}")
                    break
        
        print(f"📥 [SyncService] Retrieved {len(all_txs)} raw items from QBO.")
        
        # [MODIFIED v4.3.2] GLOBAL PURGE: To enforce "Zero Suggestions" policy strictly,
        # we clear any non-history/non-rule suggestions for all unmatched transactions in this realm.
        from app.models.qbo import Transaction
        self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.status == 'unmatched',
            Transaction.matching_method.in_(['none', None, 'ai']) # Purge legacy suggestions
        ).update({
            "suggested_category_name": None,
            "suggested_category_id": None,
            "suggested_payee": None,
            "confidence": None,
            "reasoning": None,
            "matching_method": 'none',
            "vendor_reasoning": None,
            "category_reasoning": None,
            "tax_deduction_note": None
        }, synchronize_session=False)
        self.db.commit()
        print(f"🧹 [SyncService] Global Suggestion Purge Complete.")
        
        # [NEW] Report Fallback for Hidden Transfers
        try:
            # We use the same start date effectively
            # Format today for end_date
            end_date = date.today().isoformat()
            report_txs = await self._fetch_missing_via_report(start_date[:10], end_date, active_account_ids)
            if report_txs:
                all_txs.extend(report_txs)
        except Exception as e:
            print(f"⚠️ Report Sync Wrapper failed: {e}")
        
        synced_ids = set()
        valid_count = 0
        
        for p in all_txs:
            acc_id = self._resolve_account_id(p, active_account_ids)
            if not acc_id:
                # DEBUG: Trace skipped items
                amt = p.get("TotalAmt") or p.get("Amount") or 0
                if float(amt) > 6000 and float(amt) < 6100:
                    print(f"❌ SKIPPED TARGET! ID: {p.get('Id')} | Entity: {p.get('_source_entity')} | Amt: {amt}")
                    print(f"   - AccountRef: {p.get('AccountRef')}")
                    print(f"   - FromAccountRef: {p.get('FromAccountRef')}")
                    print(f"   - ToAccountRef: {p.get('ToAccountRef')}")
                    print(f"   - DepositToAccountRef: {p.get('DepositToAccountRef')}")
                continue

            valid_count += 1
            synced_ids.add(str(p["Id"]))
            
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
            
            tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
            tx.account_id = acc_id
            tx.account_name = self._resolve_account_name(p)
            
            # DESCRIPTION LOGIC: Prioritize existing description/memo
            # If empty, fallback to Vendor/Payee name (Suggestion)
            tx.description = self._resolve_description(p)
            
            tx.amount = p.get("TotalAmt") or p.get("Amount") or 0
            tx.currency = p.get("CurrencyRef", {}).get("value", "USD")
            
            # Tag transaction type
            tx.transaction_type = p.get("_source_entity", "Purchase")
            if p.get("_source_entity") == "Purchase" and p.get("PaymentType") == "Check":
                tx.transaction_type = "Check"
            elif p.get("_source_entity") == "Purchase" and p.get("PaymentType") == "CreditCard":
                tx.transaction_type = "CreditCard"
            tx.sync_token = p.get("SyncToken")
            tx.note = p.get("PrivateNote")
            tx.payee = self._resolve_payee(p, acc_id)
            tx.raw_json = p

            # Check for duplicates using fuzzy logic (Hubdoc Standard)
            # [DISABLED TEMPORARILY FOR DEBUG SPEED]
            # dup_id, dup_conf = self._check_duplicates(tx)
            # if dup_id:
            #     print(f"⚠️ [Duplicate] Potential duplicate found for {tx.id} -> {dup_id} ({dup_conf})")
            #     tx.potential_duplicate_id = dup_id
            #     tx.duplicate_confidence = dup_conf
            #     tx.status = "potential_duplicate" # Prevent auto-categorization

            # LOGGING TARGET
            if tx.amount > 6000 and tx.amount < 6100:
                print(f"🎯 PROCESSING TARGET: ID {tx.id} | Date {tx.date} | Desc {tx.description} | Amt {tx.amount} | Type {tx.transaction_type} | Acc {tx.account_id}")


            is_qbo_matched, _ = FeedLogic.analyze(p)
            tx.is_qbo_matched = is_qbo_matched
            
            # [MODIFIED v4.3.1] Strict "Zero Suggestions" Policy
            # Every sync/re-sync starts with a clean slate. 
            # Suggestions ONLY populate if History/Rules find a match in AnalysisService.
            tx.suggested_category_name = None
            tx.suggested_category_id = None
            tx.suggested_payee = None
            tx.confidence = None
            tx.reasoning = None
            tx.matching_method = 'none'
            tx.vendor_reasoning = None
            tx.category_reasoning = None
            tx.tax_deduction_note = None

            self.db.add(tx)
        
        # Pruning
        if synced_ids:
            self.db.query(Transaction).filter(
                Transaction.realm_id == self.connection.realm_id,
                Transaction.id.notin_(synced_ids)
            ).delete(synchronize_session=False)

        self.db.commit()
        self._log("sync", "transaction", valid_count, "success")

    def _resolve_account_id(self, p, active_ids):
        # Priority 1: Check standard references
        # [MODIFIED v4.3] Iterate to find the *Active* one.
        # Previously we just took the first one and checked if it was active, which failed for Transfers (From vs To).
        potential_keys = ["AccountRef", "DepositToAccountRef", "FromAccountRef", "ToAccountRef"]
        
        for key in potential_keys:
            if key in p:
                 candidate_id = str(p[key].get("value"))
                 if candidate_id in active_ids:
                     return candidate_id
        
        # Priority 2: Payment specifics
        if "CheckPayment" in p and "BankAccountRef" in p["CheckPayment"]:
            cid = str(p["CheckPayment"]["BankAccountRef"].get("value"))
            if cid in active_ids: return cid
            
        if "CreditCardPayment" in p and "CCAccountRef" in p["CreditCardPayment"]:
            cid = str(p["CreditCardPayment"]["CCAccountRef"].get("value"))
            if cid in active_ids: return cid
            
        # [FIX] Handle CreditCardPayment Entity directly (top-level keys)
        if "CCAccountRef" in p:
            cid = str(p["CCAccountRef"].get("value"))
            if cid in active_ids: return cid
            
        if "BankAccountRef" in p:
             cid = str(p["BankAccountRef"].get("value"))
             if cid in active_ids: return cid
            
        return None

    def _resolve_account_name(self, p):
        if "AccountRef" in p: return p["AccountRef"].get("name")
        if "DepositToAccountRef" in p: return p["DepositToAccountRef"].get("name")
        # etc...
        return "Unknown Account"

    def _resolve_vendor_name(self, p):
        name = p.get("EntityRef", {}).get("name") or p.get("VendorRef", {}).get("name") or p.get("CustomerRef", {}).get("name")
        if not name and "Line" in p and len(p["Line"]) > 0:
            name = p["Line"][0].get("Description")
        return name or "Uncategorized Expense"

    def _resolve_description(self, p):
        # 1. Line Description (most accurate for line-item detail)
        if "Line" in p and len(p["Line"]) > 0:
            desc = p["Line"][0].get("Description")
            if desc and desc.strip():
                return desc
        
        # 2. PrivateNote (Memo)
        # User Request: "check if there is a memo we can put in there instead"
        private_note = p.get("PrivateNote")
        if private_note and private_note.strip():
            return private_note
            
        return None

    def _resolve_payee(self, p, active_acc_id=None):
        """
        Resolves the full hierarchical name if possible.
        Fallback for Transfers: Use the counterpart account name.
        """
        ref = p.get("EntityRef") or p.get("VendorRef") or p.get("CustomerRef")
        
        # Priority 1: Standard QBO Entity (Vendor/Customer)
        if ref:
            name = ref.get("name")
            val = ref.get("value")
            
            if val:
                # Try to look up fully_qualified_name from our DB
                from app.models.qbo import Vendor, Customer
                entity = self.db.query(Vendor).filter(Vendor.id == val).first()
                if not entity:
                    entity = self.db.query(Customer).filter(Customer.id == val).first()
                
                if entity and entity.fully_qualified_name:
                    return entity.fully_qualified_name
            return name

        # Priority 2: Fallback for Transfers/CreditCardPayments (No EntityRef)
        # Use the name of the OTHER account involved in the transaction.
        entity_type = p.get("_source_entity")
        if entity_type in ["Transfer", "CreditCardPayment"]:
            other_acc_name = self._resolve_counterpart_account_name(p, active_acc_id)
            if other_acc_name:
                return f"Transfer: {other_acc_name}"

        return None

    def _resolve_counterpart_account_name(self, p, active_acc_id):
        """Finds the name of the account that is NOT the active_acc_id."""
        # Check common transfer/payment account pairs
        pairs = [
            ("FromAccountRef", "ToAccountRef"),
            ("AccountRef", "DepositToAccountRef"),
            ("BankAccountRef", "CCAccountRef"), # CheckPayment vs CreditCardPayment
        ]
        
        # Flattened list of all account refs to check
        all_refs = [
            p.get("FromAccountRef"), p.get("ToAccountRef"),
            p.get("AccountRef"), p.get("DepositToAccountRef"),
            p.get("CCAccountRef"), p.get("BankAccountRef")
        ]
        # Also check nested refs
        if "CheckPayment" in p: all_refs.append(p["CheckPayment"].get("BankAccountRef"))
        if "CreditCardPayment" in p: all_refs.append(p["CreditCardPayment"].get("CCAccountRef"))

        for r in all_refs:
            if r and r.get("value") and str(r.get("value")) != str(active_acc_id):
                return r.get("name")
        
        return None

    def _extract_category(self, p):
        if "Line" in p:
            for line in p["Line"]:
                for detail_key in ["AccountBasedExpenseLineDetail", "JournalEntryLineDetail", "DepositLineDetail", "SalesItemLineDetail"]:
                    if detail_key in line:
                        detail = line[detail_key]
                        # AccountBasedExpense uses AccountRef
                        # SalesItem uses ItemAccountRef
                        ref = detail.get("AccountRef") or detail.get("ItemAccountRef")
                        if ref and ref.get("name") and "Uncategorized" not in ref.get("name"):
                            return ref.get("value"), ref.get("name")
        return None, None

    async def sync_categories(self):
        # Sync Expenses, Income, and Other types to give AI full context
        data = await self.client.query("SELECT * FROM Account WHERE AccountType IN ('Expense', 'Other Expense', 'Income', 'Other Income')")
        accounts = data.get("QueryResponse", {}).get("Account", [])
        for a in accounts:
            cat = self.db.query(Category).filter(Category.id == a["Id"]).first()
            if not cat:
                cat = Category(id=a["Id"], realm_id=self.connection.realm_id)
            cat.name = a["Name"]
            cat.type = a["AccountType"]
            self.db.add(cat)
        self.db.commit()

    async def sync_customers(self):
        data = await self.client.query("SELECT * FROM Customer")
        customers = data.get("QueryResponse", {}).get("Customer", [])
        for c in customers:
            cust = self.db.query(Customer).filter(Customer.id == c["Id"]).first()
            if not cust:
                cust = Customer(id=c["Id"], realm_id=self.connection.realm_id)
            cust.display_name = c["DisplayName"]
            cust.fully_qualified_name = c.get("FullyQualifiedName")
            self.db.add(cust)
        self.db.commit()

    async def sync_vendors(self):
        data = await self.client.query("SELECT * FROM Vendor")
        vendors = data.get("QueryResponse", {}).get("Vendor", [])
        for v in vendors:
            vend = self.db.query(Vendor).filter(Vendor.id == v["Id"]).first()
            if not vend:
                vend = Vendor(id=v["Id"], realm_id=self.connection.realm_id)
            vend.display_name = v["DisplayName"]
            vend.fully_qualified_name = v.get("FullyQualifiedName")
            
            # Enrich with extra_data (Hubdoc/Dext Style)
            vend.extra_data = {
                "address": v.get("BillAddr"),
                "email": v.get("PrimaryEmailAddr", {}).get("Address"),
                "phone": v.get("PrimaryPhone", {}).get("FreeFormNumber"),
                "account_ref": v.get("TermRef", {}).get("name") # Default terms/category clues
            }
            self.db.add(vend)
        self.db.commit()

    def _resolve_account_name(self, p):
        # 1. Direct Ref
        for ref_key in ["AccountRef", "DepositToAccountRef", "FromAccountRef"]:
            if ref_key in p: return p[ref_key].get("name")
        
        # 2. Payment specifics
        if "CheckPayment" in p and "BankAccountRef" in p["CheckPayment"]:
            return p["CheckPayment"]["BankAccountRef"].get("name")
        if "CreditCardPayment" in p and "CCAccountRef" in p["CreditCardPayment"]:
            return p["CreditCardPayment"]["CCAccountRef"].get("name")
        
        # 3. Bank Account specifics
        if "Line" in p:
            for line in p["Line"]:
                for detail in ["AccountBasedExpenseLineDetail", "DepositLineDetail"]:
                    if detail in line and "AccountRef" in line[detail]:
                        return line[detail]["AccountRef"].get("name")

        return "Unknown Account"

    def _check_duplicates(self, tx):
        """
        Hubdoc-style Fuzzy Duplicate Detection:
        - Exact Amount (or inverted for credit/debit mix-ups)
        - Date +/- 2 days
        - Different ID
        """
        from datetime import timedelta
        
        # Define search window
        date_start = tx.date - timedelta(days=2)
        date_end = tx.date + timedelta(days=2)
        
        # Query potential matches
        candidates = self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.date >= date_start,
            Transaction.date <= date_end,
            Transaction.id != tx.id,
            # Optimisation: Check amount in Python or DB? DB is faster.
            Transaction.amount == tx.amount 
        ).all()
        
        if candidates:
            # Found exact amount match in date range
            best_match = candidates[0]
            confidence = 0.95 if best_match.date == tx.date else 0.85
            return best_match.id, confidence
            
        # Check inverted amount (e.g. 100.00 vs -100.00)
        candidates_inv = self.db.query(Transaction).filter(
            Transaction.realm_id == self.connection.realm_id,
            Transaction.date >= date_start,
            Transaction.date <= date_end,
            Transaction.id != tx.id,
            Transaction.amount == -tx.amount 
        ).all()
        
        if candidates_inv:
            best_match = candidates_inv[0]
            confidence = 0.80
            return best_match.id, confidence

        return None, None

    async def _fetch_missing_via_report(self, start_date: str, end_date: str, active_account_ids: list[str]) -> list:
        """
        Fallback Strategy: Fetch TransactionList report to find Transfers/CreditCardPayments
        that are hidden by API queries due to Inactive Source Accounts.
        """
        print(f"📊 [SyncService] Fetching TransactionList Report for backup sync ({start_date} to {end_date})...")
        
        endpoint = "reports/TransactionList"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "columns": "tx_date,txn_type,doc_num,name,memo,amount,account_name",
            # We can't strictly filter by transaction_type in reports easily without stripping others, 
            # but we can filter in memory.
        }
        
        recovered_items = []
        
        try:
            res = await self.client.request("GET", endpoint, params=params)
            rows = res.get("Rows", {}).get("Row", [])
            
            print(f"📊 [SyncService] Report Check: Found {len(rows)} rows.")
            
            # Helper to extract ID
            def get_col_val(cols, idx): # Safety
                 if idx < len(cols): return cols[idx].get("value")
                 return ""

            for row in rows:
                if "ColData" not in row: continue
                cols = row["ColData"]
                
                # Extract ID (usually in hidden 'id' attribute of the first or type column)
                target_id = None
                txn_type_str = ""
                # DEBUG ROW
                if "116" in str(row):
                     print(f"🔎 DEBUG REPORT ROW 116: {cols}")
                
                for col in cols:
                    val = col.get("value")
                    # Strict Type Check & ID Extraction
                    if val in ["Transfer", "Credit Card Payment"]:
                        txn_type_str = val
                        if col.get("id"):
                            target_id = col.get("id")
                
                if not target_id:
                     # print("   -> No ID found in row")
                     continue
                     
                if not txn_type_str:
                     continue
                
                # Check if we already have it locally
                exists = self.db.query(Transaction).filter(Transaction.id == target_id).first()
                if exists: 
                    # print(f"   -> ID {target_id} ({txn_type_str}) already exists.")
                    continue
                
                print(f"⚠️ [Report] ID {target_id} ({txn_type_str}) is MISSING locally! Attempting recovery...")
                
                # Determine Entity Type for Fetch
                entity_type = "Transfer"
                if "Credit Card" in txn_type_str:
                    entity_type = "CreditCardPayment"
                elif "Transfer" in txn_type_str:
                    entity_type = "Transfer"
                else:
                    continue # Skip other types
                
                print(f"detecting missing {entity_type} {target_id} from report...")
                
                # Fetch Full Entity
                try:
                     full_tx = await self.client.get_entity(target_id, entity_type)
                     
                     tx_data = None
                     if entity_type == "CreditCardPayment":
                         tx_data = full_tx.get("CreditCardPayment")
                         # [FALLBACK] Report says "Credit Card Payment" but API says "Transfer"
                         if not tx_data:
                             print(f"⚠️ [SyncService] ID {target_id} returned no CreditCardPayment data. Trying Transfer...")
                             full_tx_transfer = await self.client.get_entity(target_id, "Transfer")
                             tx_data = full_tx_transfer.get("Transfer")
                             if tx_data: 
                                 entity_type = "Transfer" # Correct the type
                             
                     elif entity_type == "Transfer":
                         tx_data = full_tx.get("Transfer")
                         
                     if tx_data:
                         
                         # Check if it involves an ACTIVE account
                         acc_id = self._resolve_account_id(tx_data, active_account_ids)
                         if acc_id:
                             print(f"✅ [SyncService] Recovering hidden {entity_type} {target_id} for Account {acc_id}!")
                             tx_data["_source_entity"] = entity_type
                             recovered_items.append(tx_data)
                         else:
                             # It's a transfer between two inactive accounts? Ignore.
                             pass
                except Exception as e:
                    print(f"⚠️ [SyncService] Failed to fetch details for {target_id}: {e}")
                    
        except Exception as e:
            print(f"❌ [SyncService] Report sync failed: {e}")
            
        print(f"📥 [SyncService] Recovered {len(recovered_items)} items via Report.")
        return recovered_items
