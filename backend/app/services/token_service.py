from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user import User

class TokenService:
    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: str) -> int:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.token_balance

    def has_sufficient_tokens(self, user_id: str, cost: int) -> bool:
        balance = self.get_balance(user_id)
        return balance >= cost

    def deduct_tokens(self, user_id: str, cost: int, reason: str = "usage") -> bool:
        """
        Deducts tokens from user. Returns True if successful, False if insufficient funds.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.token_balance < cost:
            return False
            
        user.token_balance -= cost
        self.db.add(user)
        self.db.commit()
        
        # In a real system, we'd log this transaction to a 'token_ledger' table
        print(f"💰 Tokens deducted: {cost} for '{reason}'. New Balance: {user.token_balance}")
        
        return True

    def refill_tokens(self, user_id: str, amount: int):
        """
        Refills tokens (e.g., monthly reset or purchase).
        Ideally resets to allowance, or adds to it depending on policy.
        Here we implement 'Reset to Allowance' policy for monthly cycles.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return
            
        user.token_balance = amount
        user.last_refill_date = datetime.now()
        self.db.add(user)
        self.db.commit()
