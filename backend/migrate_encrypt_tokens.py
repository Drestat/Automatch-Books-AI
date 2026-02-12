"""
One-time migration script: encrypt existing plaintext OAuth tokens in the database.

Run this ONCE after deploying the encryption code and setting FERNET_KEY:
  python migrate_encrypt_tokens.py

It uses the decrypt_token fallback (which returns plaintext if it can't decrypt)
to detect already-encrypted vs plaintext tokens and only encrypts those that
haven't been encrypted yet.
"""
import os
import sys

# Add parent dir so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User  # register FK
from app.models.qbo import QBOConnection
from app.core.encryption import encrypt_token, decrypt_token
from cryptography.fernet import Fernet, InvalidToken

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    fernet_key = os.getenv("FERNET_KEY")
    if not fernet_key:
        print("❌ FERNET_KEY not set")
        return

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    connections = session.query(QBOConnection).all()
    print(f"Found {len(connections)} QBO connections")

    f = Fernet(fernet_key.encode())
    migrated = 0

    for conn in connections:
        changed = False

        # Check if refresh_token is already encrypted
        if conn.refresh_token:
            try:
                f.decrypt(conn.refresh_token.encode())
                # Already encrypted
            except InvalidToken:
                # Plaintext — encrypt it
                conn.refresh_token = encrypt_token(conn.refresh_token)
                changed = True

        # Check if access_token is already encrypted
        if conn.access_token:
            try:
                f.decrypt(conn.access_token.encode())
            except InvalidToken:
                conn.access_token = encrypt_token(conn.access_token)
                changed = True

        if changed:
            migrated += 1
            print(f"  🔒 Encrypted tokens for realm {conn.realm_id}")

    if migrated > 0:
        session.commit()
        print(f"✅ Migrated {migrated} connections")
    else:
        print("✅ All tokens are already encrypted (no migration needed)")

    session.close()

if __name__ == "__main__":
    main()
