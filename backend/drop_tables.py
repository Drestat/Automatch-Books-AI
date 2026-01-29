from sqlalchemy import create_engine, text
from app.core.config import settings

def drop_transactions_table():
    if not settings.DATABASE_URL:
        print("DATABASE_URL not set")
        return

    db_url = settings.DATABASE_URL
    if "sslmode" not in db_url:
        db_url += "?sslmode=require"
        
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Dropping transactions table...")
        conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        conn.commit()
        print("Dropped.")

if __name__ == "__main__":
    drop_transactions_table()
