from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# CRITICAL: Use NullPool for serverless compatibility
# External PgBouncer (or cloud provider's pooler) handles connection pooling
# This prevents connection exhaustion from ephemeral Modal functions
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Disable SQLAlchemy's internal pooling
    connect_args={
        "connect_timeout": 10,  # 10 second connection timeout
        # NOTE: statement_timeout removed - Neon pooler doesn't support it in startup options
        # Set timeouts per-session or per-query if needed
    },
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
