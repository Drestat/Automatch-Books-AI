from app.db.session import SessionLocal
from app.services.gamification_service import GamificationService
from app.models.qbo import QBOConnection
from app.models.user import User

def check_gamification():
    db = SessionLocal()
    try:
        # 1. Provide a real user ID
        # Since we don't know the exact user ID from here easily without querying QBOConnection or User
        # Let's grabbing the first QBOConnection's user_id
        conn = db.query(QBOConnection).first()
        if not conn:
            print("❌ No QBO Connection found.")
            return

        user_id = conn.user_id
        print(f"👤 Checking stats for User ID: {user_id}")

        service = GamificationService(db)
        stats = service.get_user_stats(user_id)
        
        print(f"🔥 Current Streak: {stats.current_streak}")
        print(f"🏆 Total XP: {stats.total_xp}")
        print(f"🎖️ Current Level: {stats.current_level}")
        print(f"📅 Last Activity: {stats.last_activity_date}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_gamification()
