
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.qbo import Transaction
from app.core.config import settings

# Setup DB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("🔍 Checking for transactions with Amount = 0.00 or None...")

zero_txs = db.query(Transaction).filter((Transaction.amount == 0) | (Transaction.amount == None)).all()
print(f"Found {len(zero_txs)} transactions with 0 amount.")

for tx in zero_txs:
    print(f" - [{tx.date}] {tx.description} (ID: {tx.id}) | Status: {tx.status} | Payee: {tx.payee}")

# Specific check for Pam Seitz - fuzzy match or specific check
pam_txs = db.query(Transaction).filter(Transaction.description.ilike("%Pam Seitz%")).all()
print(f"\n🔍 Checking 'Pam Seitz' transactions ({len(pam_txs)} found):")
for tx in pam_txs:
    print(f" - [{tx.date}] {tx.description} (IDs: {tx.id}) | Amount: {tx.amount} | Status: {tx.status}")

db.close()
