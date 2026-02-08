from app.db.session import SessionLocal
from app.models.user import User
from app.models.qbo import QBOConnection

def check_all_tokens():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"🔍 Found {len(users)} users")
        
        for user in users:
            print(f"👤 User: {user.id} | Email: {user.email} | Balance: {user.token_balance}")
            
        connections = db.query(QBOConnection).all()
        print(f"🔗 Found {len(connections)} connections")
        for conn in connections:
             print(f"🏢 Realm: {conn.realm_id} | UserID: {conn.user_id}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_all_tokens()
