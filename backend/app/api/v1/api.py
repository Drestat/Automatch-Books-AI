from fastapi import APIRouter
from app.api.v1.endpoints import qbo, transactions

api_router = APIRouter()
api_router.include_router(qbo.router, prefix="/qbo", tags=["qbo"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
