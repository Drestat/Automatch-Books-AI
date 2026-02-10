from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.gamification_service import GamificationService

router = APIRouter()

@router.get("/stats")
async def get_my_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current user's gamification stats (HUD).
    """
    service = GamificationService(db)
    stats = service.get_user_stats(current_user.id)
    return {
        "user_id": stats.user_id,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "total_xp": stats.total_xp,
        "current_level": stats.current_level,
        "last_activity_date": stats.last_activity_date
    }

@router.get("/history")
async def get_my_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get recent gamification events (XP history).
    """
    service = GamificationService(db)
    events = service.get_recent_events(current_user.id, limit=limit)
    return events
