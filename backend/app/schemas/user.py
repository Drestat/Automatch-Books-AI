from pydantic import BaseModel
from typing import Optional

class UserSync(BaseModel):
    id: str
    email: str
    stripe_customer_id: Optional[str] = None

class UserPreferences(BaseModel):
    auto_accept_enabled: bool
