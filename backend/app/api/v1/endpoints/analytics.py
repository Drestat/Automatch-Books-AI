from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.qbo import QBOConnection
from app.services.analytics_service import AnalyticsService
from app.services.ai_analyzer import AIAnalyzer
from app.services.token_service import TokenService
from app.models.user import User
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import datetime

router = APIRouter()

# --- Schema Definitions ---
class TrackEventRequest(BaseModel):
    event_name: str
    properties: Optional[Dict[str, Any]] = None
    user_id: str 

class AnalyticsEventSchema(BaseModel):
    id: str
    user_id: str
    event_name: str
    properties: Optional[Dict[str, Any]]
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/")
def get_dashboard_analytics(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    realm_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Restored Endpoint: Returns aggregated stats for the User Dashboard.
    Resolves Realm ID from User ID if not provided.
    """
    target_realm = realm_id
    
    # Try to resolve realm from user_id if realm_id is missing
    if not target_realm and x_user_id:
        connection = db.query(QBOConnection).filter(QBOConnection.user_id == x_user_id).first()
        if connection:
            target_realm = connection.realm_id
            
    if not target_realm:
        # Fallback for demo mode or unconnected users (return empty structure/error)
        # However, useAnalytics handles demo mode on frontend now.
        # If we reach here, we expect a real connection.
        return {"error": "User not connected to QBO"}

    service = AnalyticsService(db, target_realm)
    return service.get_dashboard_stats()

@router.post("/track")
def track_event(
    event: TrackEventRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Telemetry: Stores user actions permanently.
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent")

    db_event = AnalyticsEvent(
        user_id=event.user_id,
        event_name=event.event_name,
        properties=event.properties,
        ip_address=ip,
        user_agent=user_agent
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"status": "success", "id": str(db_event.id)}

@router.get("/events", response_model=List[AnalyticsEventSchema])
def get_events(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Admin: Fetch raw event logs.
    """
    events = db.query(AnalyticsEvent).order_by(AnalyticsEvent.timestamp.desc()).limit(limit).all()
    return [AnalyticsEventSchema(
        id=str(e.id),
        user_id=e.user_id,
        event_name=e.event_name,
        properties=e.properties,
        timestamp=e.timestamp
    ) for e in events]

@router.post("/insights")
def generate_insights(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin AI: Generates strategic insights using Gemini Flash.
    Cost: 25 Tokens.
    """
    COST = 25
    token_service = TokenService(db)
    
    if not token_service.has_sufficient_tokens(current_user.id, COST):
        return {"error": "Insufficient tokens. Upgrade to Pro/Business."}

    # 1. Fetch recent events
    events = db.query(AnalyticsEvent).order_by(AnalyticsEvent.timestamp.desc()).limit(limit).all()
    
    if not events:
        return {"error": "No events found to analyze"}
        
    # 2. Call AI Analyzer
    analyzer = AIAnalyzer()
    insights = analyzer.generate_insights(events)
    
    # 3. Deduct if successful
    if "error" not in insights:
         token_service.deduct_tokens(current_user.id, COST, "AI Insights Report")
    
    return insights

@router.get("/admin/usage")
def get_all_usage(db: Session = Depends(get_db)):
    """
    Admin: Aggregated usage across all connected realms.
    """
    service = AnalyticsService(db, realm_id="") # realm_id not used for this method
    return service.get_all_user_usage()
