import os
import json
import requests
from dotenv import load_dotenv, set_key
from intuitlib.client import AuthClient

load_dotenv()

class QBOClient:
    def __init__(self):
        self.client_id = os.getenv("QBO_CLIENT_ID")
        self.client_secret = os.getenv("QBO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QBO_REDIRECT_URI")
        self.environment = os.getenv("QBO_ENVIRONMENT", "sandbox")
        self.refresh_token = os.getenv("QBO_REFRESH_TOKEN")
        self.company_id = os.getenv("QBO_COMPANY_ID")
        
        # Clean quotes if they exist in .env
        if self.refresh_token: self.refresh_token = self.refresh_token.strip("'").strip('"')
        if self.company_id: self.company_id = self.company_id.strip("'").strip('"')

        self.auth_client = AuthClient(
            self.client_id,
            self.client_secret,
            self.redirect_uri,
            self.environment,
            refresh_token=self.refresh_token,
            realm_id=self.company_id
        )
        self.access_token = None

    def _refresh_access_token(self):
        print("🔄 Refreshing QBO Access Token...")
        self.auth_client.refresh()
        self.access_token = self.auth_client.access_token
        # Update refresh token in .env if it changed
        set_key(".env", "QBO_REFRESH_TOKEN", self.auth_client.refresh_token)
        return self.access_token

    def _get_headers(self):
        if not self.access_token:
            self._refresh_access_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def _get_api_url(self, endpoint):
        base_url = "https://sandbox-quickbooks.api.intuit.com" if self.environment == "sandbox" else "https://quickbooks.api.intuit.com"
        return f"{base_url}/v3/company/{self.company_id}/{endpoint}"

    def query(self, sql_query):
        url = self._get_api_url("query")
        headers = self._get_headers()
        params = {'query': sql_query}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 401: # Unauthorized/Expired
            self._refresh_access_token()
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            
        response.raise_for_status()
        return response.json()

    def get_bank_transactions(self):
        query = "SELECT * FROM Purchase"
        return self.query(query).get("QueryResponse", {}).get("Purchase", [])

    def get_categories(self):
        query = "SELECT * FROM Account WHERE AccountType = 'Expense'"
        return self.query(query).get("QueryResponse", {}).get("Account", [])

    def get_customers(self):
        query = "SELECT * FROM Customer"
        return self.query(query).get("QueryResponse", {}).get("Customer", [])

    def update_purchase_category(self, purchase_id, category_id, sync_token):
        """Processes a write-back to categorize an existing Purchase"""
        url = self._get_api_url("purchase")
        headers = self._get_headers()
        
        # First, we need to get the existing purchase to ensure we have the full object
        # QBO updates are usually full-object PUTs
        existing = self.query(f"SELECT * FROM Purchase WHERE Id = '{purchase_id}'").get("QueryResponse", {}).get("Purchase", [None])[0]
        if not existing:
            raise ValueError(f"Purchase {purchase_id} not found in QBO")

        # Update the AccountRef (The category)
        existing["AccountRef"] = {"value": category_id}
        # QBO requires Sparse update or full object
        payload = existing
        
        response = requests.post(url, headers=headers, json=payload, params={'operation': 'update'})
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    client = QBOClient()
    try:
        res = client.get_bank_transactions()
        print(f"📊 Found {len(res)} transactions in QBO.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
