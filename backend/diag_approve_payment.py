
import asyncio
import os
import psycopg2
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, Transaction
from app.services.qbo_client import QBOClient
from app.services.transaction_service import TransactionService
from dotenv import load_dotenv
import json

load_dotenv()

async def debug_approve_payment(realm_id, tx_id):
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("❌ Connection not found")
            return

        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if not tx:
            print(f"❌ Transaction {tx_id} not found locally")
            return

        print(f"🔍 Transaction found: {tx.description} ({tx.transaction_type}) - Amount: {tx.amount}")
        print(f"   SyncToken: {tx.sync_token}")
        
        client = QBOClient(db, connection)
        
        # Simulate what TransactionService.approve_match does (or approve_transaction)
        # Since it's a "Match" (is_qbo_matched=True likely? Or logic found a match?)
        # If it was "Cool Cars", it was likely unmatched in DB until recently.
        # If the user clicked "Approve Match", it means the UI showed a match.
        
        # Let's try calling update_purchase directly with the Payment logic
        
        print("\nAttempting update_purchase (as Payment)...")
        try:
            # For Payments, we expect it to use the 'payment' endpoint
            # checking logic in QBOClient.update_purchase
            
            # We assume it goes through update_purchase
            res = await client.update_purchase(
                purchase_id=tx.id,
                category_id=None, # Payments don't have category usually, or it's implied by invoice
                category_name=None,
                sync_token=tx.sync_token,
                entity_type="Payment",
                entity_ref={"value": "8", "name": "0969 Ocean View Road"}, # Example customer from previous diag
                note="Test Approval Note",
                append_memo="#Accepted"
            )
            print("✅ Update Successful!")
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"❌ Update Failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_approve_payment('9341456245321396', '61'))
