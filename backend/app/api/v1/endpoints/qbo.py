from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.qbo import QBOConnection
from app.models.user import User
from app.core.config import settings
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import secrets

router = APIRouter()

@router.get("/authorize")
def authorize(user_id: str):
    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        redirect_uri=settings.QBO_REDIRECT_URI,
        environment=settings.QBO_ENVIRONMENT,
    )
    scopes = [Scopes.ACCOUNTING]
    auth_url = auth_client.get_authorization_url(scopes, state_token=user_id)
    return {"auth_url": auth_url}

@router.get("/callback")
def callback(code: str, state: str, realmId: str, db: Session = Depends(get_db)):
    auth_client = AuthClient(
        client_id=settings.QBO_CLIENT_ID,
        client_secret=settings.QBO_CLIENT_SECRET,
        redirect_uri=settings.QBO_REDIRECT_URI,
        environment=settings.QBO_ENVIRONMENT,
    )
    auth_client.get_bearer_token(code, realm_id=realmId)
    
    # State holds the user_id in this implementation
    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realmId).first()
    if not connection:
        connection = QBOConnection(user_id=user.id, realm_id=realmId)
    
    connection.refresh_token = auth_client.refresh_token
    connection.access_token = auth_client.access_token
    db.add(connection)
    db.commit()
    
    return {"message": "QuickBooks connected successfully", "realm_id": realmId}
