
import pytest
from datetime import date, timedelta
from app.services.gamification_service import GamificationService
from app.models.gamification import UserGamificationStats
from app.models.user import User

@pytest.fixture
def test_user(db_session):
    # Ensure user exists for FK constraint
    user = db_session.query(User).filter(User.id == "game_test_user").first()
    if not user:
        user = User(id="game_test_user", email="game@test.com", subscription_tier="free")
        db_session.add(user)
        db_session.commit()
    return user

@pytest.fixture
def gamification_service(db_session):
    return GamificationService(db_session)

class TestGamificationLogic:

    def test_xp_values(self, gamification_service, test_user):
        """
        Verify new XP values:
        - Categorize: 10 XP
        - Receipt Upload: 20 XP
        - Weekly Streak: 100 XP (tested separately)
        """
        # Reset stats
        stats = gamification_service.get_user_stats(test_user.id)
        stats.total_xp = 0
        gamification_service.db.commit()

        # Test Categorize (10 XP)
        res = gamification_service.add_xp(test_user.id, "categorize")
        assert res["new_xp"] == 10
        
        # Test Receipt (20 XP)
        res = gamification_service.add_xp(test_user.id, "receipt_upload")
        assert res["new_xp"] == 30 # 10 + 20

    def test_weekly_streak_increment(self, gamification_service, test_user, db_session):
        """
        Test: Streak increments if last activity was in the PREVIOUS ISO week.
        """
        stats = gamification_service.get_user_stats(test_user.id)
        
        # Setup: Last activity was exactly 1 week ago (Previous ISO Week)
        # Using specific date calculation to ensure ISO week boundary crossing is reliable?
        # Let's just use `today - 7 days`. Unless today is Monday and 7 days ago was also Monday...
        # Wait, ISO week is Mon-Sun.
        # If today is Mon (Day 1), 7 days ago was Mon (Day 1 of prev week). YES.
        
        today = date.today()
        last_week_day = today - timedelta(days=7)
        
        stats.last_activity_date = last_week_day
        stats.current_streak = 1
        stats.longest_streak = 1
        db_session.commit()
        
        # Action: Trigger activity today
        # We allow update via helper or add_xp
        result = gamification_service._update_streak(stats)
        
        # Logic: If last activity was Previous ISO Week, new streak should be 2.
        # Currently the code calculates DAILY, so expect failure until implementation.
        assert result["streak_updated"] is True
        assert stats.current_streak == 2

    def test_weekly_streak_same_period(self, gamification_service, test_user, db_session):
        """
        Test: Streak does NOT increment if already active this ISO week.
        """
        stats = gamification_service.get_user_stats(test_user.id)
        
        today = date.today()
        # Active yesterday (same ISO week unless today is Monday)
        # To be safe, let's just use `today`.
        
        stats.last_activity_date = today
        stats.current_streak = 5
        db_session.commit()
        
        result = gamification_service._update_streak(stats)
        
        assert result["streak_updated"] is False
        assert stats.current_streak == 5

    def test_weekly_streak_reset(self, gamification_service, test_user, db_session):
        """
        Test: Streak resets to 1 if last activity was > 1 week ago (missed a full week).
        """
        stats = gamification_service.get_user_stats(test_user.id)
        
        # 2 weeks ago
        two_weeks_ago = date.today() - timedelta(days=14)
        
        stats.last_activity_date = two_weeks_ago
        stats.current_streak = 10
        db_session.commit()
        
        result = gamification_service._update_streak(stats)
        
        # Should reset to 1
        assert result["streak_updated"] is True
        assert stats.current_streak == 1

