import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.api.deps import get_current_user
from app.models.qbo import User
from app.services.stripe_service import StripeService
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.post("/checkout")
def create_checkout(
    success_url: str,
    cancel_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = StripeService(db)
    return service.create_checkout_session(current_user, success_url, cancel_url)

@router.post("/portal")
def create_portal(
    return_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = StripeService(db)
    return service.create_portal_session(current_user, return_url)

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        customer_id = session.get('customer')
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.stripe_customer_id = customer_id
            user.subscription_status = 'active'
            user.subscription_tier = 'pro'
            # Calculate trial end if present
            if session.get('subscription_data', {}).get('trial_end'):
                 # Note: Timestamp from Stripe is unix epoch
                 ts = session.get('subscription_data', {}).get('trial_end')
                 user.trial_ends_at = datetime.fromtimestamp(ts)
            
            db.add(user)
            db.commit()
            
    elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted']:
        sub = event['data']['object']
        customer_id = sub.get('customer')
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = sub.get('status') # active, past_due, canceled
            db.add(user)
            db.commit()

    return {"status": "success"}
