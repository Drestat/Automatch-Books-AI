
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.gamification_service import GamificationService

router = APIRouter()

@router.get("/stats")
def get_user_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get gamification stats (XP, Level, Streak) for the current user.
    """
    service = GamificationService(db)
    stats = service.get_user_stats(current_user.id)
    
    # Calculate next level progress
    # Simple logic: Thresholds are 0, 100, 250...
    # We need to find next threshold.
    next_level_xp = 0
    current_level_base_xp = 0
    
    # Sort thresholds
    thresholds = sorted(service.LEVEL_THRESHOLDS.items())
    
    for level, xp in thresholds:
        if level > stats.current_level:
            next_level_xp = xp
            break
        current_level_base_xp = xp
        
    if next_level_xp == 0:
        # Max level?
        next_level_xp = stats.total_xp # 100% progress
        
    progress_xp = stats.total_xp - current_level_base_xp
    required_xp = next_level_xp - current_level_base_xp
    
    progress_percent = 0
    if required_xp > 0:
        progress_percent = min(100, int((progress_xp / required_xp) * 100))

    return {
        "current_level": stats.current_level,
        "total_xp": stats.total_xp,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "last_activity_date": stats.last_activity_date,
        "next_level_xp": next_level_xp,
        "progress_percent": progress_percent
    }

@router.get("/leaderboard")
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get global leaderboard sorted by Total XP.
    """
    from app.models.gamification import UserGamificationStats
    from sqlalchemy import desc
    
    # query top users
    results = db.query(UserGamificationStats).order_by(desc(UserGamificationStats.total_xp)).limit(limit).all()
    
    leaderboard = []
    for r in results:
        # Get user email/name (masked?)
        user = db.query(User).filter(User.id == r.user_id).first()
        name = "Anonymous"
        if user:
            if user.email:
                name = user.email.split("@")[0] # Simple masking
        
        leaderboard.append({
            "user_id": r.user_id,
            "name": name,
            "level": r.current_level,
            "xp": r.total_xp,
            "is_me": r.user_id == current_user.id
        })
        
    return leaderboard
