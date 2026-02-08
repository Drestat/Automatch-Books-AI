from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
db = SessionLocal()
con = db.query(QBOConnection).first()
if con:
    print(f"REALM_ID: {con.realm_id}")
else:
    print("NO CONNECTIONS FOUND")
db.close()
