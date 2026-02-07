import os
import sys
from datetime import datetime, timedelta
import uuid

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.sync_service import SyncService

def test_duplicate_logic():
    db = SessionLocal()
    realm_id = "9341456245321396" # Sandbox Realm

    # 1. Setup: Create a base transaction
    base_id = str(uuid.uuid4())
    base_date = datetime.now()
    base_tx = Transaction(
        id=base_id,
        realm_id=realm_id,
        date=base_date,
        description="Base Transaction",
        amount=100.00,
        currency="USD",
        status="unmatched"
    )
    db.merge(base_tx)
    db.commit()
    print(f"✅ Created Base Transaction: {base_id} ($100.00)")

    # 2. Test Exact Match (Same Amount, Same Date)
    dup_id = str(uuid.uuid4())
    dup_tx = Transaction(
        id=dup_id,
        realm_id=realm_id,
        date=base_date,
        description="Duplicate Transaction",
        amount=100.00,
        currency="USD"
    )
    
    # Mocking connection
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    service = SyncService(db, connection)
    
    match_id, conf = service._check_duplicates(dup_tx)
    if match_id == base_id:
        print(f"✅ Exact Match Detected! Confidence: {conf}")
    else:
        print(f"❌ Exact Match FAILED. Got: {match_id}")

    # 3. Test Fuzzy Match (Same Amount, Date + 1 day)
    fuzzy_id = str(uuid.uuid4())
    fuzzy_tx = Transaction(
        id=fuzzy_id,
        realm_id=realm_id,
        date=base_date + timedelta(days=1),
        description="Fuzzy Transaction",
        amount=100.00,
        currency="USD"
    )
    
    match_id, conf = service._check_duplicates(fuzzy_tx)
    if match_id == base_id:
        print(f"✅ Fuzzy Match Detected! Confidence: {conf}")
    else:
        print(f"❌ Fuzzy Match FAILED. Got: {match_id}")

    # 4. Test No Match (Different Amount)
    diff_id = str(uuid.uuid4())
    diff_tx = Transaction(
        id=diff_id,
        realm_id=realm_id,
        date=base_date,
        description="Different Transaction",
        amount=50.00,
        currency="USD"
    )
    
    match_id, conf = service._check_duplicates(diff_tx)
    if not match_id:
        print(f"✅ No Match Correctly Identified")
    else:
        print(f"❌ False Positive! Matched with: {match_id}")

    # Cleanup
    db.query(Transaction).filter(Transaction.id.in_([base_id, dup_id, fuzzy_id, diff_id])).delete()
    db.commit()

if __name__ == "__main__":
    test_duplicate_logic()
