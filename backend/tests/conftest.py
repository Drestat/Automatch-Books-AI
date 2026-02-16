"""
Shared test fixtures and configuration for pytest.

This file provides reusable fixtures for:
- Database sessions (SQLite in-memory)
- Test users and QBO connections
- Mock external APIs (QBO, Stripe, Gemini, Modal)
- Sample test data (transactions, categories, etc.)
"""

import os
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set testing environment variables BEFORE importing app parts
# This ensures pydantic settings and database engine initialize correctly for tests
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
if not os.environ.get("FERNET_KEY"):
    os.environ["FERNET_KEY"] = "7l8j1_yR8e8K9Vb9d8v9X8Z8_8k8j8l8j1_yR8e8K9U=" # Dummy key for testing

# Import app components
from app.db.session import Base
from app.main import app
from app.api.deps import get_db


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a test database engine using SQLite in-memory.

    Scope: session (created once for all tests)
    This avoids the cost of PostgreSQL for unit tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create an isolated database session for each test.

    Scope: function (fresh session for each test)
    Automatically rolls back changes after test completes.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """
    Create FastAPI TestClient with overridden database dependency.

    Use this for integration tests of API endpoints.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# USER & AUTH FIXTURES
# ============================================================================

@pytest.fixture
def test_user(db_session):
    """
    Create a test user with professional subscription tier.
    """
    from app.models.user import User

    user = User(
        id="test_user_123",
        email="test@example.com",
        token_balance=1000,
        monthly_token_allowance=2000,
        subscription_tier="professional",
        subscription_status="active",
        stripe_customer_id="cus_test_456",
        auto_accept_enabled=False,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_free_tier(db_session):
    """
    Create a test user with free tier (for testing subscription limits).
    """
    from app.models.user import User

    user = User(
        id="test_user_free",
        email="free@example.com",
        token_balance=25,
        monthly_token_allowance=25,
        subscription_tier="free",
        subscription_status="active",
        auto_accept_enabled=False,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_qbo_connection(db_session, test_user):
    """
    Create a test QuickBooks Online connection.
    """
    from app.models.qbo import QBOConnection
    from app.core.encryption import encrypt_token

    connection = QBOConnection(
        realm_id="test_realm_123",
        user_id=test_user.id,
        access_token=encrypt_token("test_access_token_encrypted"),
        refresh_token=encrypt_token("test_refresh_token_encrypted"),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(connection)
    db_session.flush()
    db_session.refresh(connection)
    return connection


@pytest.fixture
def auth_headers(test_user):
    """
    Create authentication headers for API requests.
    """
    return {"X-User-Id": test_user.id}


# ============================================================================
# TRANSACTION & CATEGORY FIXTURES
# ============================================================================

@pytest.fixture
def base_transaction(db_session, test_qbo_connection):
    """
    Create a base transaction for duplicate detection tests.
    """
    from app.models.qbo import Transaction

    tx = Transaction(
        id="tx_base_001",
        realm_id=test_qbo_connection.realm_id,
        date=datetime(2024, 1, 15).date(),
        description="Test Transaction",
        amount=100.00,
        currency="USD",
        status="unmatched",
        transaction_type="Purchase",
        account_id="acc_001",
        sync_token="0",
        created_at=datetime.utcnow()
    )
    db_session.add(tx)
    db_session.flush()
    db_session.refresh(tx)
    return tx


@pytest.fixture
def sample_categories(db_session, test_qbo_connection):
    """
    Create sample expense categories.
    """
    from app.models.qbo import Category

    categories = [
        Category(
            id="cat_001",
            realm_id=test_qbo_connection.realm_id,
            name="Office Supplies",
            type="Expense"
        ),
        Category(
            id="cat_002",
            realm_id=test_qbo_connection.realm_id,
            name="Travel Expenses",
            type="Expense"
        ),
        Category(
            id="cat_003",
            realm_id=test_qbo_connection.realm_id,
            name="Utilities",
            type="Expense"
        ),
    ]
    db_session.add_all(categories)
    db_session.flush()
    return categories


@pytest.fixture
def sample_bank_account(db_session, test_qbo_connection):
    """
    Create sample bank account.
    """
    from app.models.qbo import BankAccount

    account = BankAccount(
        id="acc_001",
        realm_id=test_qbo_connection.realm_id,
        name="Business Checking",
        nickname="Main Account",
        balance=25000.00,
        currency="USD",
        is_active=True,
        is_connected=True
    )
    db_session.add(account)
    db_session.flush()
    db_session.refresh(account)
    return account


# ============================================================================
# SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def sync_service(db_session, test_qbo_connection, mock_qbo_client):
    """
    Create SyncService instance with test dependencies.
    """
    from app.services.sync_service import SyncService
    return SyncService(db_session, test_qbo_connection)


@pytest.fixture
def transaction_service(db_session, test_qbo_connection):
    """
    Create TransactionService instance.
    """
    from app.services.transaction_service import TransactionService
    return TransactionService(db_session, test_qbo_connection)


@pytest.fixture
def receipt_service(db_session, test_qbo_connection):
    """
    Create ReceiptService instance.
    """
    from app.services.receipt_service import ReceiptService
    return ReceiptService(db_session, test_qbo_connection.realm_id)


# ============================================================================
# EXTERNAL API MOCKS
# ============================================================================

@pytest.fixture
def qbo_mock_responses():
    """
    Load mock QuickBooks API responses from fixtures.
    """
    fixtures_path = Path(__file__).parent / "fixtures" / "qbo_responses.json"
    if fixtures_path.exists():
        with open(fixtures_path) as f:
            return json.load(f)

    # Return minimal mock data if file doesn't exist yet
    return {
        "purchase_transaction": {
            "Purchase": {
                "Id": "123",
                "TxnDate": "2024-01-15",
                "TotalAmt": 150.50,
                "SyncToken": "0"
            }
        },
        "query_purchases": {
            "QueryResponse": {
                "Purchase": [],
                "maxResults": 1000
            }
        }
    }


@pytest.fixture
def mock_qbo_client(qbo_mock_responses):
    """
    Mock QBOClient with realistic API responses.
    """
    with patch('app.services.qbo_client.QBOClient') as MockClient, \
         patch('app.services.sync_service.QBOClient', new=MockClient):
        mock_instance = AsyncMock()

        async def mock_query(query_str):
            if "Purchase" in query_str:
                return qbo_mock_responses["query_purchases"]
            return {"QueryResponse": {}}

        async def mock_get(endpoint):
            return qbo_mock_responses.get("purchase_transaction", {})

        async def mock_post(endpoint, data):
            # Return the posted data with an ID
            return {**data, "Id": "new_123", "SyncToken": "0"}

        async def mock_update(endpoint, data):
            # Return updated data with incremented sync token
            return {**data, "SyncToken": str(int(data.get("SyncToken", "0")) + 1)}

        mock_instance.query.side_effect = mock_query
        mock_instance.get.side_effect = mock_get
        mock_instance.post.side_effect = mock_post
        mock_instance.update.side_effect = mock_update

        MockClient.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_modal_workers():
    """
    Automatically mock Modal workers to prevent actual cloud execution.

    This fixture runs automatically for all tests (autouse=True).
    """
    with patch('modal_app.sync_user_data.spawn') as mock_sync, \
         patch('modal_app.process_ai_categorization.spawn') as mock_ai, \
         patch('modal_app.process_single_approval.spawn') as mock_approval, \
         patch('modal_app.bulk_approve_modal.spawn') as mock_bulk:

        # Make spawn methods return immediately
        mock_sync.return_value = None
        mock_ai.return_value = None
        mock_approval.return_value = None
        mock_bulk.return_value = None

        yield {
            "sync": mock_sync,
            "ai": mock_ai,
            "approval": mock_approval,
            "bulk": mock_bulk
        }


@pytest.fixture
def mock_gemini_api():
    """
    Mock Google Gemini API for AI categorization.
    """
    with patch('google.generativeai.GenerativeModel') as MockModel:
        mock_model = AsyncMock()

        async def fake_generate(prompt, **kwargs):
            # Return deterministic categorization based on prompt keywords
            prompt_lower = prompt.lower()

            if "office" in prompt_lower or "supplies" in prompt_lower:
                category = "Office Supplies"
                confidence = 0.90
            elif "travel" in prompt_lower or "uber" in prompt_lower:
                category = "Travel Expenses"
                confidence = 0.85
            elif "food" in prompt_lower or "restaurant" in prompt_lower:
                category = "Meals & Entertainment"
                confidence = 0.88
            else:
                category = "General Expenses"
                confidence = 0.70

            response_json = {
                "category": category,
                "confidence": confidence,
                "reasoning": f"Test reasoning for {category}"
            }

            # Mock response object
            mock_response = AsyncMock()
            mock_response.text = json.dumps(response_json)
            return mock_response

        mock_model.generate_content_async.side_effect = fake_generate
        MockModel.return_value = mock_model
        yield mock_model


@pytest.fixture
def stripe_mock_events():
    """
    Load mock Stripe webhook events.
    """
    fixtures_path = Path(__file__).parent / "fixtures" / "stripe_events.json"
    if fixtures_path.exists():
        with open(fixtures_path) as f:
            return json.load(f)

    # Return minimal mock data if file doesn't exist yet
    return {
        "checkout_session_completed": {
            "id": "evt_test_webhook",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_456",
                    "client_reference_id": "test_user_123",
                    "amount_total": 2900,
                    "metadata": {
                        "tier": "professional",
                        "tokens": "2000"
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_stripe_webhook_signature():
    """
    Generate valid Stripe webhook signature for testing.
    """
    import hmac
    import hashlib
    import time

    def create_signature(payload: str, secret: str = "test_webhook_secret") -> str:
        """Generate valid Stripe webhook signature"""
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    return create_signature


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def sample_receipt_data():
    """
    Sample extracted receipt data for testing.
    """
    return {
        "merchant": "Staples",
        "total": 45.99,
        "date": "2024-01-15",
        "items": [
            {"description": "Paper", "amount": 20.00},
            {"description": "Pens", "amount": 15.99},
            {"description": "Tax", "amount": 10.00}
        ],
        "confidence": 0.92
    }


@pytest.fixture
def caplog(caplog):
    """
    Capture log output for assertions.

    Usage:
        def test_something(caplog):
            some_function()
            assert "Expected log message" in caplog.text
    """
    return caplog


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_env():
    """
    Clean up environment variables after each test.
    """
    yield
    # Reset testing flag
    os.environ["TESTING"] = "true"
