import stripe
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.api.deps import get_current_user
from app.models.user import User
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

def _sync_clerk_metadata(user_id: str, status: str, tier: str):
    """
    Syncs subscription status back to Clerk so the Next.js middleware knows the flow.
    """
    if not settings.CLERK_SECRET_KEY:
        print("⚠️ CLERK_SECRET_KEY not set - skipping metadata sync")
        return

    try:
        url = f"https://api.clerk.com/v1/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "public_metadata": {
                "subscription_status": status,
                "subscription_tier": tier
            }
        }
        res = requests.patch(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to sync Clerk metadata for user {user_id}: {str(e)}")

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
            
            # Token Refill (Based on Tier)
            # Hardcoded logic for now. Ideally fetched from price_id metadata.
            if user.subscription_tier == 'pro':
                user.monthly_token_allowance = 1000
                user.token_balance = 1000
            elif user.subscription_tier == 'business':
                 user.monthly_token_allowance = 10000
                 user.token_balance = 10000
            else:
                 user.monthly_token_allowance = 50
                 user.token_balance = 50

            
            db.add(user)
            db.commit()
            
            # Sync to Clerk
            _sync_clerk_metadata(user.id, user.subscription_status, user.subscription_tier)
            
    elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted']:
        sub = event['data']['object']
        customer_id = sub.get('customer')
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = sub.get('status') # active, past_due, canceled
            
            # Renewal Logic: If active, refill tokens
            # Identify renewal by checking if billing period started recently? 
            # Or simplified: if active, ensure balance is at least allowance.
            if user.subscription_status == 'active':
                  # In a robust system, we check invoice.payment_succeeded instead. 
                  # But for MVP, if we get an update and it's active, let's just minimal check implementation.
                  # Actually, let's leave renewal refill for 'invoice.payment_succeeded' event which we need to add.
                  pass
                  
            db.add(user)
            db.commit()
            
            # Sync to Clerk
            _sync_clerk_metadata(user.id, user.subscription_status, user.subscription_tier)

    return {"status": "success"}
