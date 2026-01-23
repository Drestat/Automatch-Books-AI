from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.api.deps import get_current_user
from app.models.qbo import User, QBOConnection
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's realm_id
    connection = db.query(QBOConnection).filter(QBOConnection.user_id == current_user.id).first()
    if not connection:
        return {"error": "No QuickBooks connection found"}
        
    service = AnalyticsService(db, connection.realm_id)
    return service.get_dashboard_stats()
