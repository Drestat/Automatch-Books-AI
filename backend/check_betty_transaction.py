"""
Script to check what's in the database for the "Books By Bessie" transaction
"""
import os
import sys
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction

db = SessionLocal()

try:
    # Find the "Sold to betty" transaction
    tx = db.query(Transaction).filter(
        Transaction.description.like('%betty%')
    ).first()
    
    if tx:
        print(f"Found transaction:")
        print(f"  ID: {tx.id}")
        print(f"  Description: {tx.description}")
        print(f"  Note: {tx.note}")
        print(f"  Payee: {tx.payee}")
        print(f"  Amount: {tx.amount}")
        print(f"  Date: {tx.date}")
        print(f"\nRaw JSON EntityRef:")
        if tx.raw_json and 'EntityRef' in tx.raw_json:
            print(f"  {tx.raw_json['EntityRef']}")
        print(f"\nRaw JSON PrivateNote:")
        if tx.raw_json:
            print(f"  {tx.raw_json.get('PrivateNote', 'N/A')}")
    else:
        print("Transaction not found")
        
finally:
    db.close()
