import requests
import time
from sqlalchemy.orm import Session
from app.models.qbo import QBOConnection
from app.core.config import settings
from intuitlib.client import AuthClient

class QBOClient:
    def __init__(self, db: Session, qbo_connection: QBOConnection):
        self.db = db
        self.connection = qbo_connection
        self.auth_client = AuthClient(
            client_id=settings.QBO_CLIENT_ID,
            client_secret=settings.QBO_CLIENT_SECRET,
            redirect_uri=settings.QBO_REDIRECT_URI,
            environment=settings.QBO_ENVIRONMENT,
            refresh_token=self.connection.refresh_token,
            realm_id=self.connection.realm_id
        )

    def _refresh_access_token(self):
        self.auth_client.refresh()
        self.connection.access_token = self.auth_client.access_token
        self.connection.refresh_token = self.auth_client.refresh_token
        self.db.add(self.connection)
        self.db.commit()
        return self.auth_client.access_token

    def _get_api_url(self, endpoint):
        base_url = "https://sandbox-quickbooks.api.intuit.com" if settings.QBO_ENVIRONMENT == "sandbox" else "https://quickbooks.api.intuit.com"
        return f"{base_url}/v3/company/{self.connection.realm_id}/{endpoint}"

    def request(self, method: str, endpoint: str, params: dict = None, json_payload: dict = None):
        """
        Unified QBO request handler with:
        - Auto-refresh for 401 Unauthorized
        - Exponential backoff for 429 Rate Limits
        """
        url = self._get_api_url(endpoint)
        headers = {
            'Authorization': f'Bearer {self.connection.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            # Using basic requests as pooling was reverted
            res = requests.request(method, url, headers=headers, params=params, json=json_payload)
            
            if res.status_code == 401:
                token = self._refresh_access_token()
                headers['Authorization'] = f'Bearer {token}'
                continue # Retry with new token
            
            if res.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"⚠️ QBO Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            res.raise_for_status()
            return res.json()

    def query(self, query_str):
        return self.request("GET", "query", params={'query': query_str})

    def revoke(self):
        """
        Revoke the refresh token on the Intuit side to terminate the connection.
        """
        try:
            print(f"🔌 [QBOClient] Revoking token for realm_id: {self.connection.realm_id}")
            self.auth_client.revoke(token=self.connection.refresh_token)
            print(f"✅ [QBOClient] Token revoked successfully.")
            return True
        except Exception as e:
            print(f"⚠️ [QBOClient] Revocation failed or already revoked: {e}")
            return False
