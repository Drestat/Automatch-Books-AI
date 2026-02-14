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
        
        synced_ids = set()
        valid_count = 0
        
        for p in all_txs:
            acc_id = self._resolve_account_id(p, active_account_ids)
            if not acc_id: continue

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
            
            tx.amount = p.get("TotalAmt", 0)
            tx.currency = p.get("CurrencyRef", {}).get("value", "USD")
            
            # Tag transaction type
            tx.transaction_type = p.get("_source_entity", "Purchase")
            if p.get("_source_entity") == "Purchase" and p.get("PaymentType") == "Check":
                tx.transaction_type = "Check"
            elif p.get("_source_entity") == "Purchase" and p.get("PaymentType") == "CreditCard":
                tx.transaction_type = "CreditCard"
            tx.sync_token = p.get("SyncToken")
            tx.note = p.get("PrivateNote")
            tx.payee = self._resolve_payee(p)
            tx.raw_json = p

            # Check for duplicates using fuzzy logic (Hubdoc Standard)
            dup_id, dup_conf = self._check_duplicates(tx)
            if dup_id:
                print(f"⚠️ [Duplicate] Potential duplicate found for {tx.id} -> {dup_id} ({dup_conf})")
                tx.potential_duplicate_id = dup_id
                tx.duplicate_confidence = dup_conf
                tx.status = "potential_duplicate" # Prevent auto-categorization


            is_qbo_matched, _ = FeedLogic.analyze(p)
            tx.is_qbo_matched = is_qbo_matched
            
            # Extract existing category if present
            qbo_cat_id, qbo_cat_name = self._extract_category(p)
            
            # [MODIFIED v4.2] Disable QBO Auto-Cat Import per user request.
            # We want Antigravity AI to be the sole source of truth.
            # if qbo_cat_name and tx.status not in ['pending_approval', 'approved']:
            #     tx.suggested_category_name = qbo_cat_name
            #     tx.suggested_category_id = qbo_cat_id
            #     tx.confidence = 0.9
            #     tx.reasoning = f"Imported existing category '{qbo_cat_name}' from QuickBooks."

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
        if "AccountRef" in p:
            id = str(p["AccountRef"].get("value"))
        elif "DepositToAccountRef" in p:
            id = str(p["DepositToAccountRef"].get("value"))
        elif "FromAccountRef" in p:
            id = str(p["FromAccountRef"].get("value"))
        elif "CheckPayment" in p and "BankAccountRef" in p["CheckPayment"]:
            id = str(p["CheckPayment"]["BankAccountRef"].get("value"))
        elif "CreditCardPayment" in p and "CCAccountRef" in p["CreditCardPayment"]:
            id = str(p["CreditCardPayment"]["CCAccountRef"].get("value"))
        else:
            return None
        return id if id in active_ids else None

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
        
        # 2. Strict: Do NOT fallback to PrivateNote or VendorName.
        # User wants manual control or explicit suggestion click.
        return None

    def _resolve_payee(self, p):
        """
        Resolves the full hierarchical name if possible.
        """
        ref = p.get("EntityRef") or p.get("VendorRef") or p.get("CustomerRef")
        if not ref: return None
        
        name = ref.get("name")
        val = ref.get("value")
        
        if val:
            # Try to look up fully_qualified_name from our DB
            from app.models.qbo import Vendor, Customer
            # Note: We don't necessarily know if it's a Vendor or Customer from the Ref alone sometimes
            # but usually it's one of them.
            entity = self.db.query(Vendor).filter(Vendor.id == val).first()
            if not entity:
                entity = self.db.query(Customer).filter(Customer.id == val).first()
            
            if entity and entity.fully_qualified_name:
                return entity.fully_qualified_name
        
        return name

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
