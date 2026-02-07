import os
import sys
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection, VendorAlias, ClassificationRule, Vendor, Category
from app.services.analysis_service import AnalysisService

def test_rules_and_aliases():
    db = SessionLocal()
    realm_id = "9341456245321396"

    # Setup: Create Category and Vendor
    cat_id = str(uuid.uuid4())
    cat = Category(id=cat_id, realm_id=realm_id, name="Auto Expenses", type="Expense")
    db.merge(cat)
    
    vend_id = str(uuid.uuid4())
    vend = Vendor(id=vend_id, realm_id=realm_id, display_name="Amazon")
    db.merge(vend)
    
    # 1. Test Vendor Alias
    # "Amzn Mktp 123" -> "Amazon"
    alias_id = str(uuid.uuid4())
    alias = VendorAlias(id=alias_id, realm_id=realm_id, alias="Amzn Mktp", vendor_id=vend_id)
    db.merge(alias)
    db.commit()
    print("✅ Created Vendor Alias: 'Amzn Mktp' -> 'Amazon'")

    service = AnalysisService(db, realm_id)
    resolved = service._resolve_vendor_alias("Amzn Mktp Ref 12345")
    
    if resolved == "Amazon":
        print(f"✅ Alias Resolution Works: 'Amzn Mktp Ref 12345' -> {resolved}")
    else:
        print(f"❌ Alias Resolution Failed. Got: {resolved}")

    # 2. Test Classification Rule
    # "Uber" -> "Auto Expenses" + Tag "Weekend"
    rule_id = str(uuid.uuid4())
    rule = ClassificationRule(
        id=rule_id,
        realm_id=realm_id,
        name="Uber Rule",
        priority=10,
        conditions={"description_contains": "Uber"},
        action={"category": "Auto Expenses", "tag": "Weekend"}
    )
    db.merge(rule)
    db.commit()
    print("✅ Created Rule: 'Uber' -> 'Auto Expenses'")

    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        realm_id=realm_id,
        date=datetime.now(),
        description="Uber Trip 999",
        amount=15.00,
        currency="USD",
        tags=[]
    )
    
    match = service._apply_rules(tx)
    
    if match and tx.suggested_category_name == "Auto Expenses" and "Weekend" in tx.tags:
        print(f"✅ Rule Logic Works! Cat: {tx.suggested_category_name}, Tags: {tx.tags}")
    else:
        print(f"❌ Rule Logic Failed. Cat: {tx.suggested_category_name}, Tags: {tx.tags}")

    # Cleanup
    db.delete(alias)
    db.delete(rule)
    db.delete(cat)
    db.delete(vend)
    db.commit()

if __name__ == "__main__":
    test_rules_and_aliases()
