import requests
import json
import os
import sys

# Mock connection data or just use existing ones
sys.path.append(os.getcwd())
from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection

def test_requests_upload():
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == "104").first()
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    
    realm_id = connection.realm_id
    access_token = connection.access_token
    
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/upload"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    filename = "test.png"
    content_type = "image/png"
    file_bytes = tx.receipt_content
    
    metadata = {
        "ContentType": content_type,
        "FileName": filename,
        "AttachableRef": [{"EntityRef": {"type": "BillPayment", "value": "104"}}]
    }
    
    files = {
        'file_metadata_01': (None, json.dumps(metadata), 'application/json'),
        'file_content_01': (None, file_bytes, content_type)
    }
    
    print(f"Uploading via requests to {url}...")
    # Use requests.post
    res = requests.post(url, headers=headers, files=files)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test_requests_upload()
