import os
import secrets
from flask import Flask, request, redirect
from dotenv import load_dotenv, set_key
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration from .env
CLIENT_ID = os.getenv("QBO_CLIENT_ID")
CLIENT_SECRET = os.getenv("QBO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("QBO_REDIRECT_URI", "http://localhost:8080/callback")
ENVIRONMENT = os.getenv("QBO_ENVIRONMENT", "sandbox")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Error: QBO_CLIENT_ID and QBO_CLIENT_SECRET must be set in .env")
    exit(1)

auth_client = AuthClient(
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    ENVIRONMENT
)

@app.route('/')
def index():
    scopes = [Scopes.ACCOUNTING]
    auth_url = auth_client.get_authorization_url(scopes)
    return f'<h1>QBO Auth Helper</h1><p><a href="{auth_url}">Click here to authorize with QuickBooks</a></p>'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    realm_id = request.args.get('realmId')
    
    if not code:
        return 'No code provided', 400
    
    auth_client.get_bearer_token(code, realm_id=realm_id)
    refresh_token = auth_client.refresh_token
    
    # Update .env with the new tokens
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("")
            
    set_key(env_path, "QBO_REFRESH_TOKEN", refresh_token)
    set_key(env_path, "QBO_COMPANY_ID", realm_id)
    
    return f'<h2>Success!</h2><p>Refresh Token saved to .env</p><p>Realm ID: {realm_id}</p>'

if __name__ == "__main__":
    print(f"🚀 Starting Auth Helper on {REDIRECT_URI}...")
    print("Please ensure your Redirect URI in the Intuit Developer Portal matches this.")
    app.run(port=8080)
