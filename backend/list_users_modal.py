import asyncio
from app.db.session import SessionLocal
from app.models.user import User
from sqlalchemy import select

async def main():
    db = SessionLocal()
    try:
        stmt = select(User)
        result = db.execute(stmt)
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Tier: {user.subscription_tier}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
