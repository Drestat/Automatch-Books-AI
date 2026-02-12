import modal
import os
from dotenv import dotenv_values
import json
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("qbo-cli")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

config = dotenv_values(os.path.join(base_dir, ".env"))
qbo_secrets = modal.Secret.from_dict({
    "DATABASE_URL": config.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": config.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": config.get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": config.get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": config.get("QBO_REDIRECT_URI", ""),
    "FERNET_KEY": config.get("FERNET_KEY", "")
})

@app.function(image=image, secrets=[qbo_secrets])
def query(sql_query: str):
    """
    Executes a QBO SQL query and prints the results.
    Usage: modal run qbo_cli.py::query --sql-query "SELECT * FROM Vendor MAXRESULTS 5"
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User # Register User model for FK
    from app.models.qbo import QBOConnection
    from intuitlib.client import AuthClient
    import requests
    
    # 1. Database Connection
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("❌ No QBO connection found in database.")
        print("   Please run the auth flow first.")
        return

    # 2. Setup Auth Client
    client_id = os.getenv("QBO_CLIENT_ID")
    client_secret = os.getenv("QBO_CLIENT_SECRET")
    environment = os.getenv("QBO_ENVIRONMENT", "sandbox")
    redirect_uri = os.getenv("QBO_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")
    
    auth_client = AuthClient(
        client_id=client_id,
        client_secret=client_secret,
        environment=environment,
        redirect_uri=redirect_uri,
    )
    
    # 3. Refresh Token
    try:
        from app.core.encryption import decrypt_token, encrypt_token
        auth_client.refresh(refresh_token=decrypt_token(conn.refresh_token))
        # Update DB with new encrypted tokens
        conn.access_token = encrypt_token(auth_client.access_token)
        conn.refresh_token = encrypt_token(auth_client.refresh_token)
        session.commit()
    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        return

    # 4. Execute Query
    realm_id = conn.realm_id
    base_url = "https://sandbox-quickbooks.api.intuit.com" if environment == "sandbox" else "https://quickbooks.api.intuit.com"
    url = f"{base_url}/v3/company/{realm_id}/query"
    
    headers = {
        "Authorization": f"Bearer {auth_client.access_token}",
        "Accept": "application/json",
        "Content-Type": "application/text"
    }
    
    print(f"\n📡 Executing Query: {sql_query}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, headers=headers, params={"query": sql_query})
        
        if response.status_code == 200:
            data = response.json()
            query_response = data.get("QueryResponse", {})
            
            if not query_response:
                print("⚠️  No data returned (Empty Response)")
            else:
                total_count = query_response.get("totalCount")
                if total_count is not None:
                     print(f"🔢 Total Count: {total_count}")
                
                for key, value in query_response.items():
                    if key not in ["startPosition", "maxResults", "totalCount"]:
                        print(f"✅ Found {len(value)} {key}(s):")
                        for item in value:
                            id_val = item.get("Id", "N/A")
                            name = item.get("DisplayName", item.get("Name", "N/A"))
                            print(f"   - [ID: {id_val}] {name}")
                            if len(value) <= 5:
                                print(f"     {json.dumps(item, indent=2)}")
                        
        else:
            print(f"❌ Query Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error executing request: {e}")
    finally:
        print(f"{'='*80}\n")

@app.function(image=image, secrets=[qbo_secrets])
def inspect_id(entity: str, entity_id: str):
    """
    Fetches a specific QBO entity by ID.
    Usage: modal run qbo_cli.py::inspect_id --entity Vendor --entity-id 56
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User # Register User model for FK
    from app.models.qbo import QBOConnection
    from intuitlib.client import AuthClient
    import requests
    import json
    
    # 1. Database Connection
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("❌ No QBO connection found.")
        return

    # 2. Auth
    client_id = os.getenv("QBO_CLIENT_ID")
    client_secret = os.getenv("QBO_CLIENT_SECRET")
    environment = os.getenv("QBO_ENVIRONMENT", "sandbox")
    redirect_uri = os.getenv("QBO_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")
    
    auth_client = AuthClient(
        client_id=client_id,
        client_secret=client_secret,
        environment=environment,
        redirect_uri=redirect_uri,
    )
    try:
        from app.core.encryption import decrypt_token, encrypt_token
        auth_client.refresh(refresh_token=decrypt_token(conn.refresh_token))
        conn.access_token = encrypt_token(auth_client.access_token)
        conn.refresh_token = encrypt_token(auth_client.refresh_token)
        session.commit()
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        return

    # 3. Request
    realm_id = conn.realm_id
    base_url = "https://sandbox-quickbooks.api.intuit.com" if environment == "sandbox" else "https://quickbooks.api.intuit.com"
    url = f"{base_url}/v3/company/{realm_id}/{entity.lower()}/{entity_id}"
    
    headers = {
        "Authorization": f"Bearer {auth_client.access_token}",
        "Accept": "application/json"
    }
    
    print(f"\n🔍 Inspecting {entity} ID: {entity_id}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Request Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print(f"{'='*80}\n")
