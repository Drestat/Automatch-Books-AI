from fastapi import APIRouter
from app.api.v1.endpoints import qbo, transactions, stripe_routes, analytics, users, qbo_webhooks, accounts

api_router = APIRouter()
api_router.include_router(qbo.router, prefix="/qbo", tags=["qbo"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(stripe_routes.router, prefix="/stripe", tags=["stripe"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(qbo_webhooks.router, prefix="/qbo-webhooks", tags=["qbo-webhooks"])
