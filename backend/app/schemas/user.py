from pydantic import BaseModel
from typing import Optional

class UserSync(BaseModel):
    id: str
    email: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None

class UserPreferences(BaseModel):
    auto_accept_enabled: bool
