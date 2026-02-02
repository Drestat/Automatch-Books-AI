import os
import sys
import json
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction
from app.api.v1.endpoints.transactions import TransactionSchema

def test_api_serialization():
    db = SessionLocal()
    try:
        # Get Tania's Nursery (ID 134)
        tx = db.query(Transaction).filter(Transaction.id == "134").first()
        
        if tx:
            print(f"DB Instance - ID: {tx.id}, is_qbo_matched: {tx.is_qbo_matched}")
            
            # Serialize using Pydantic schema
            schema_data = TransactionSchema.from_orm(tx)
            json_data = jsonable_encoder(schema_data)
            
            print("\nSerialized JSON:")
            print(json.dumps(json_data, indent=2))
        else:
            print("❌ Transaction 134 not found.")

    finally:
        db.close()

if __name__ == "__main__":
    test_api_serialization()
