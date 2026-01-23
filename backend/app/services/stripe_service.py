import stripe
from app.core.config import settings
from app.models.user import User
from sqlalchemy.orm import Session

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    def __init__(self, db: Session):
        self.db = db

    def create_checkout_session(self, user: User, success_url: str, cancel_url: str):
        """Creates a Stripe Checkout Session for a new subscription"""
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=user.email,
                line_items=[
                    {
                        'price': settings.STRIPE_MONTHLY_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user.id),
                subscription_data={
                    'trial_period_days': 7,
                },
                metadata={
                    "user_id": str(user.id)
                }
            )
            return {"url": checkout_session.url}
        except Exception as e:
            raise ValueError(f"Stripe Error: {str(e)}")

    def create_portal_session(self, user: User, return_url: str):
        """Creates a billing portal session for managing subscription"""
        if not user.stripe_customer_id:
            raise ValueError("User has no associated Stripe Customer ID")

        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )
            return {"url": portal_session.url}
        except Exception as e:
            raise ValueError(f"Stripe Portal Error: {str(e)}")
