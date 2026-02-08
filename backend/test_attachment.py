import asyncio
from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.qbo_client import QBOClient
from app.services.transaction_service import TransactionService
import json

async def test_attachment():
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == '133').first()
    if not tx:
        # Fallback to any recent transaction with receipt
        tx = db.query(Transaction).filter(Transaction.receipt_content != None).order_by(Transaction.date.desc()).first()
        if not tx:
            print("❌ No transactions with receipts found in DB")
            return
            
    print(f"Targeting: {tx.description} (ID: {tx.id})")
    conn = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    
    if not tx.receipt_content:
        print("❌ No receipt content for tx 66")
        return

    client = QBOClient(db, conn)
    ts = TransactionService(db, conn)
    
    print(f"Testing attachment for {tx.id} ({tx.transaction_type})")
    
    # Manually trigger upload
    try:
        # We'll use the internal _upload_receipt logic but with more logging
        file_bytes = tx.receipt_content
        filename = "test_receipt.png"
        ct = "image/png"
        
        qbo_entity_type = ts._map_to_qbo_attachable_type(tx.transaction_type or "Purchase")
        attachable_ref = {"EntityRef": {"type": qbo_entity_type, "value": tx.id}}
        
        print(f"Ref: {attachable_ref}")
        
        result = await client.upload_attachment(
            file_bytes=file_bytes,
            filename=filename,
            content_type=ct,
            attachable_ref=attachable_ref
        )
        print(f"✅ Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(test_attachment())
