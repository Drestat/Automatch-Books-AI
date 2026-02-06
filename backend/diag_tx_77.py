
import asyncio
from app.api.v1.endpoints.qbo import get_db
from app.models.qbo import Transaction, QBOConnection
from app.services.qbo_client import QBOClient

async def diagnose_tx_77():
    db = next(get_db())
    tx_id = "77"
    
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        print(f"Transaction {tx_id} not found in DB")
        return
        
    conn = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    client = QBOClient(db, conn)
    
    print(f"--- Diagnosing Transaction {tx.id} ---")
    print(f"Raw JSON keys: {list(tx.raw_json.keys()) if tx.raw_json else 'None'}")
    
    # Check Account
    cat_id = tx.category_id or tx.suggested_category_id
    if cat_id:
        print(f"Checking Account {cat_id}...")
        try:
            acc = await client.request("GET", f"account/{cat_id}")
            print(f"✅ Account {cat_id} found: {acc.get('Account', {}).get('Name')} (Active: {acc.get('Account', {}).get('Active')})")
        except Exception as e:
            print(f"❌ Account {cat_id} NOT FOUND or Error: {e}")
            
    # Check Vendor
    payee_name = tx.payee or tx.suggested_payee
    if payee_name:
        print(f"Checking Vendor for '{payee_name}'...")
        vendor = await client.get_vendor_by_name(payee_name)
        if vendor:
            print(f"✅ Vendor found: {vendor.get('DisplayName')} (Id: {vendor.get('Id')}, Active: {vendor.get('Active')})")
        else:
            print(f"❌ Vendor '{payee_name}' NOT FOUND")

    # Check Transaction itself
    print(f"Checking Purchase {tx.id} in QBO...")
    try:
        qbo_tx = await client.get_purchase(tx.id)
        purchase = qbo_tx.get("Purchase", {})
        print(f"✅ Purchase {tx.id} found in QBO.")
        print(f"SyncToken: {purchase.get('SyncToken')}")
        print(f"Lines: {len(purchase.get('Line', []))}")
        for line in purchase.get('Line', []):
            if "LinkedTxn" in line:
                print(f"🔗 Found LinkedTxn: {line['LinkedTxn']}")
                for link in line['LinkedTxn']:
                    try:
                        lt_id = link['TxnId']
                        lt_type = link['TxnType']
                        print(f"  Checking Linked {lt_type} {lt_id}...")
                        lt_res = await client.request("GET", f"{lt_type.lower()}/{lt_id}")
                        print(f"  ✅ Linked {lt_type} {lt_id} found and active.")
                    except Exception as le:
                        print(f"  ❌ Linked {lt_type} {lt_id} NOT FOUND or Error: {le}")
    except Exception as e:
        print(f"❌ Purchase {tx.id} NOT FOUND in QBO: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_tx_77())
