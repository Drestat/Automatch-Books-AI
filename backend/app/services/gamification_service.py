from datetime import date, timedelta, datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from app.models.gamification import UserGamificationStats, GamificationEvent
from app.models.user import User

class GamificationService:
    
    LEVEL_THRESHOLDS = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 1000,
        10: 2500,
        25: 7500,
        50: 15000
    }
    
    XP_VALUES = {
        "categorize": 10,
        "rule_create": 50,
        "inbox_zero": 100,
        "daily_bonus": 25
    }

    def __init__(self, db: Session):
        self.db = db

    def get_user_stats(self, user_id: str) -> UserGamificationStats:
        stats = self.db.query(UserGamificationStats).filter(UserGamificationStats.user_id == user_id).first()
        if not stats:
            # Initialize if not exists
            stats = UserGamificationStats(user_id=user_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats

    def add_xp(self, user_id: str, action_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Adds XP to user, checks for level up, and logs the event.
        """
        stats = self.get_user_stats(user_id)
        xp_amount = self.XP_VALUES.get(action_type, 0)
        
        if xp_amount == 0:
            return {"success": False, "message": "Invalid action type"}

        # Add XP
        stats.total_xp += xp_amount
        
        # Check Level Up
        old_level = stats.current_level
        new_level = self._calculate_level(stats.total_xp)
        level_up = new_level > old_level
        
        if level_up:
            stats.current_level = new_level
        
        # Log Event
        event = GamificationEvent(
            user_id=user_id,
            event_type=action_type,
            xp_earned=xp_amount,
            metadata_=metadata
        )
        self.db.add(event)
        
        # Update Streaks if applicable (e.g. first action of the day)
        streak_info = self._update_streak(stats)
        
        self.db.commit()
        self.db.refresh(stats)
        
        return {
            "new_xp": stats.total_xp,
            "level_up": level_up,
            "new_level": new_level,
            "streak_info": streak_info
        }

    def _calculate_level(self, total_xp: int) -> int:
        current_level = 1
        for level, threshold in sorted(self.LEVEL_THRESHOLDS.items()):
            if total_xp >= threshold:
                current_level = level
        return current_level

    def _update_streak(self, stats: UserGamificationStats) -> Dict[str, Any]:
        today = date.today()
        last_activity = stats.last_activity_date
        
        streak_updated = False
        
        if last_activity == today:
            # Already active today, no streak change
            pass
        elif last_activity == today - timedelta(days=1):
            # Consecutive day
            stats.current_streak += 1
            if stats.current_streak > stats.longest_streak:
                stats.longest_streak = stats.current_streak
            stats.last_activity_date = today
            streak_updated = True
        else:
            # Streak broken (or first time)
            # Check for freeze? (simplified for now: reset)
            # TODO: Implement Freeze logic usage here
            if last_activity is None:
                 stats.current_streak = 1
            else:
                 stats.current_streak = 1
            
            stats.last_activity_date = today
            streak_updated = True
            
        return {
            "current_streak": stats.current_streak,
            "streak_updated": streak_updated
        }

    def get_recent_events(self, user_id: str, limit: int = 10):
        return self.db.query(GamificationEvent)\
            .filter(GamificationEvent.user_id == user_id)\
            .order_by(desc(GamificationEvent.created_at))\
            .limit(limit)\
            .all()
