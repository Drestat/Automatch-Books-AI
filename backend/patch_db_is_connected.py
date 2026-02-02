from app.db.session import engine
from sqlalchemy import text

with engine.begin() as conn:
    print("Adding is_connected to bank_accounts...")
    conn.execute(text("ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS is_connected BOOLEAN DEFAULT FALSE;"))
    print("Done.")
