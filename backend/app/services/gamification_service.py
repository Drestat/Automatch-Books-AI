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
        "receipt_upload": 20,
        "daily_bonus": 25, # De-prioritized but kept for legacy?
        "weekly_streak_bonus": 100
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
        
        if xp_amount == 0 and action_type != "weekly_streak_keep_alive":
            # Allow Keep Alive events with 0 base XP just to update streak
            return {"success": False, "message": "Invalid action type"}
        
        # Update Streaks (Weekly Logic)
        streak_info = self._update_streak(stats)
        if streak_info["streak_updated"] and streak_info.get("bonus_awarded"):
             xp_amount += self.XP_VALUES["weekly_streak_bonus"]
             # Log the bonus separately? Or bundle it? 
             # Let's bundle for simplicity of return, but technically it's a separate event.
             # We'll just add it to total here.

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
        """
        Updates streak based on WEEKLY activity (ISO Weeks).
        """
        today = date.today()
        # Get ISO Year and Week
        current_year, current_week, _ = today.isocalendar()
        
        last_activity = stats.last_activity_date
        streak_updated = False
        bonus_awarded = False
        
        if not last_activity:
             # First time activity
             stats.current_streak = 1
             stats.longest_streak = 1
             stats.last_activity_date = today
             streak_updated = True
        else:
            last_year, last_week, _ = last_activity.isocalendar()
            
            # Calculate week difference
            is_same_week = (current_year == last_year) and (current_week == last_week)
            
            # Helper for previous week check across years
            # Simply check if today is in the week immediately following last_activity's week
            # We can approximate by days or use dateutil, but let's stick to simple logic:
            # If not same week, check if it's the *next* logical week.
            
            # Robust Check: 
            # Get Monday of current week
            current_monday = today - timedelta(days=today.weekday())
            # Get Monday of last activity week
            last_monday = last_activity - timedelta(days=last_activity.weekday())
            
            weeks_diff = (current_monday - last_monday).days / 7
            
            if is_same_week:
                # Already active this week
                pass
            elif weeks_diff == 1.0:
                # Consecutive Week!
                stats.current_streak += 1
                if stats.current_streak > stats.longest_streak:
                    stats.longest_streak = stats.current_streak
                stats.last_activity_date = today
                streak_updated = True
                bonus_awarded = True # Award XP for maintaining streak? The req says "100 xp for maintaining".
                                     # Maybe only award if streak > 1? Yes.
            else:
                # Missed a week (weeks_diff > 1)
                stats.current_streak = 1
                stats.last_activity_date = today
                streak_updated = True
            
        return {
            "current_streak": stats.current_streak,
            "streak_updated": streak_updated,
            "bonus_awarded": bonus_awarded
        }

    def get_recent_events(self, user_id: str, limit: int = 10):
        return self.db.query(GamificationEvent)\
            .filter(GamificationEvent.user_id == user_id)\
            .order_by(desc(GamificationEvent.created_at))\
            .limit(limit)\
            .all()
