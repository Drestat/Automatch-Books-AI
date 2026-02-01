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
        # Query for Bank and Credit Card accounts
        query = "SELECT * FROM Account WHERE AccountType IN ('Bank', 'Credit Card')"
        data = self.client.query(query)
        accounts = data.get("QueryResponse", {}).get("Account", [])
        
        # Sort for display stability
        accounts.sort(key=lambda x: x["Name"])

        # We sync ALL accounts so user can see them to select
        for a in accounts:
            bank = self.db.query(BankAccount).filter(
                BankAccount.id == a["Id"],
                BankAccount.realm_id == self.connection.realm_id
            ).first()
            
            if not bank:
                bank = BankAccount(id=a["Id"], realm_id=self.connection.realm_id)
                # Default is_active=False, logic elsewhere will prompt user
            
            bank.name = a["Name"]
            bank.currency = a.get("CurrencyRef", {}).get("value", "USD")
            bank.balance = a.get("CurrentBalance", 0)
            
            self.db.add(bank)
            
        self.db.commit()
        
        self._log("sync", "bank_account", len(accounts), "success", {"synced_metadata": len(accounts)})

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

        data = self.client.query("SELECT * FROM Purchase")
        purchases = data.get("QueryResponse", {}).get("Purchase", [])
        
        valid_purchases = []
        
        for p in purchases:
            # Filter by Account Limit
            account_ref = p.get("AccountRef", {})
            acc_id = account_ref.get("value")
            
            if acc_id not in self.active_account_ids:
                continue

            valid_purchases.append(p)
            
            tx = self.db.query(Transaction).filter(Transaction.id == p["Id"]).first()
            if not tx:
                tx = Transaction(id=p["Id"], realm_id=self.connection.realm_id)
            
            tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
            
            # Map Account (Source)
            tx.account_id = acc_id
            tx.account_name = account_ref.get("name", "Unknown Account")

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
            
            # Logic: If QBO has a valid category (not Uncategorized), treat as Approved History
            if qbo_category_name and "Uncategorized" not in qbo_category_name:
                tx.status = 'approved'
                tx.suggested_category_name = qbo_category_name
                tx.suggested_category_id = qbo_category_id
                tx.confidence = 1.0
                tx.confidence = 1.0
                tx.reasoning = "Imported from QBO History"
            
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

        # Update QBO via API
        payload = tx.raw_json
        
        if tx.is_split and tx.splits:
            # Multi-line split logic
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
            # Single category logic
            if not tx.suggested_category_id:
                 raise ValueError("Transaction has no suggested category")
            
            if "Line" in payload and len(payload["Line"]) > 0:
                payload["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"] = {
                    "value": tx.suggested_category_id,
                    "name": tx.suggested_category_name
                }
            else:
                payload["AccountRef"] = {"value": tx.suggested_category_id, "name": tx.suggested_category_name}
        
        res_data = self.client.request("POST", "purchase", params={'operation': 'update'}, json_payload=payload)

        # Update Mirror Status
        tx.status = 'approved'
        self.db.add(tx)
        self.db.commit()
        
        self._log("approve", "transaction", 1, "success", {"tx_id": tx_id})
        return res_data

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
