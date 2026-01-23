# Directives: Stripe Backend Implementation

To complete the monetization flow, the **Builder** must implement the following server-side logic in FastAPI.

## 1. Environment Variables
Add to `.env` (Backend) and `.env.local` (Frontend if needed):
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
BASE_URL=http://localhost:3000
```

## 2. Dependencies
Install in `backend/`:
```bash
pip install stripe
```

## 3. Database Updates (`users` table)
Add the following columns to the `users` table in `backend/app/db/tables.py` (or SQL schema):
- `stripe_customer_id` (String, nullable)
- `subscription_status` (String: 'active', 'trialing', 'past_due', 'canceled', 'unpaid')
- `subscription_tier` (String: 'freelancer', 'founder', 'empire')

## 4. API Endpoint: Create Checkout Session
**Route**: `POST /api/v1/stripe/create-checkout-session`
**Input**: `{ "price_id": "price_..." }` (or `tier_name`)

**Logic**:
1.  **Get User**: Identify user via Auth token.
2.  **Get/Create Customer**: Check if `user.stripe_customer_id` exists. If not, create Stripe Customer.
3.  **Create Session**:
    ```python
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        mode='subscription',
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=f"{BASE_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/pricing",
        subscription_data={'trial_period_days': 7},
    )
    ```
4.  **Return**: `{ "url": session.url }`

## 5. Webhook Handler
**Route**: `POST /api/v1/stripe/webhook`

**Logic**:
1.  **Verify Signature**: Use `stripe.Webhook.construct_event`.
2.  **Handle Event: `checkout.session.completed`**:
    -   Retrieve `customer_id` and `subscription_id`.
    -   Update user in DB -> `subscription_status='active'`, `subscription_tier=...`.
3.  **Handle Event: `customer.subscription.updated`**:
    -   Sync status (e.g., if trial ends or payment fails).

## 6. Frontend Integration
In `src/app/pricing/page.tsx`, update the buttons to call your new API:
```typescript
const handleSubscribe = async (tier) => {
    const res = await fetch('/api/proxy/stripe/create-checkout-session', { ... });
    const { url } = await res.json();
    window.location.href = url;
}
```
