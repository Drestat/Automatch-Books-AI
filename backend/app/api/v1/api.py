from fastapi import APIRouter
from app.api.v1.endpoints import qbo, transactions, stripe_routes

api_router = APIRouter()
api_router.include_router(qbo.router, prefix="/qbo", tags=["qbo"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(stripe_routes.router, prefix="/stripe", tags=["stripe"])
