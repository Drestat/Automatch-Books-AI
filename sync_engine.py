import os
import json
from tools.qbo_api_client import QBOClient
from tools.db_manager import DBManager

class SyncEngine:
    def __init__(self):
        self.qbo = QBOClient()
        self.db = DBManager()

    def sync_purchases(self):
        print("🔄 Syncing Purchases from QuickBooks...")
        data = self.qbo.get_bank_transactions()
        
        to_upsert = []
        for item in data:
            # Flatten for SQLite
            to_upsert.append((
                item.get("Id"),
                item.get("TxnDate"),
                item.get("AccountRef", {}).get("name", "Unknown"), # Simplified description
                float(item.get("TotalAmt", 0)),
                item.get("CurrencyRef", {}).get("value", "USD"),
                item.get("AccountRef", {}).get("value"),
                item.get("AccountRef", {}).get("name"),
                json.dumps(item)
            ))
        
        if to_upsert:
            self.db.upsert_transactions(to_upsert)
        return len(to_upsert)

    def sync_categories(self):
        print("🔄 Syncing Categories from QuickBooks...")
        data = self.qbo.get_categories()
        to_upsert = [(item.get("Id"), item.get("Name"), item.get("AccountType")) for item in data]
        if to_upsert:
            self.db.upsert_categories(to_upsert)
        return len(to_upsert)

    def sync_customers(self):
        print("🔄 Syncing Customers from QuickBooks...")
        data = self.qbo.get_customers()
        to_upsert = [(item.get("Id"), item.get("DisplayName"), item.get("FullyQualifiedName")) for item in data]
        if to_upsert:
            self.db.upsert_customers(to_upsert)
        return len(to_upsert)

    def run_full_sync(self):
        tx_count = self.sync_purchases()
        cat_count = self.sync_categories()
        cus_count = self.sync_customers()
        print(f"🚀 Full Sync Complete. mirrored {tx_count} TXs, {cat_count} Categories, {cus_count} Customers.")
        return tx_count

if __name__ == "__main__":
    engine = SyncEngine()
    engine.run_full_sync()
