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

        updated = await self.client.update_purchase(
            purchase_id=tx.id,
            category_id=tx.suggested_category_id,
            category_name=tx.suggested_category_name,
            sync_token=tx.sync_token,
            entity_ref=entity_ref,
            payment_type=payment_type,
            tags=tx.tags,
            amount=tx.amount,
            append_memo="#Accepted"
        )
        
        if updated.get("SyncToken"):
            tx.sync_token = updated.get("SyncToken")
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
                "Amount": split.amount,
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
            "TotalAmt": tx.amount,
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
