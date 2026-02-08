from app.db.session import SessionLocal
from app.models.qbo import Transaction, Vendor, Customer

def verify_enrichment():
    db = SessionLocal()
    
    # 1. Search for 55 Twin Lane
    from app.models.qbo import Vendor, Customer
    print("🔍 Searching for '55 Twin Lane'...")
    target_v = db.query(Vendor).filter(Vendor.display_name.like('%55 Twin Lane%')).first()
    if target_v:
        print(f"✅ Found in Vendors:")
        print(f"  ID: {target_v.id}")
        print(f"  Display: {target_v.display_name}")
        print(f"  Full: {target_v.fully_qualified_name}")
    
    target_c = db.query(Customer).filter(Customer.display_name.like('%55 Twin Lane%')).first()
    if target_c:
        print(f"✅ Found in Customers:")
        print(f"  ID: {target_c.id}")
        print(f"  Display: {target_c.display_name}")
        print(f"  Full: {target_c.fully_qualified_name}")
    elif not target_v:
        print("❌ Not found in Vendors or Customers.")
        
    # 2. Check Transactions for Customer 9
    print(f"\n🔍 Transactions for Customer 9 ('55 Twin Lane'):")
    # In QBO raw JSON, it might be in EntityRef or CustomerRef
    # Let's search raw_json for CustomerRef with value '9'
    txs = db.query(Transaction).filter(Transaction.realm_id == '9341456245321396').all()
    found = 0
    for tx in txs:
        raw = tx.raw_json or {}
        # Check all possible Ref locations
        refs = [raw.get('EntityRef'), raw.get('CustomerRef'), raw.get('VendorRef')]
        for r in refs:
            if r and str(r.get('value')) == '9':
                print(f"  - ID:{tx.id} | Payee:{tx.payee} | Amt:{tx.amount} | SourceEntity:{tx.transaction_type}")
                found += 1
                break
    if found == 0:
        print("  ❌ No transactions found linked to Customer ID 9.")

if __name__ == "__main__":
    verify_enrichment()
