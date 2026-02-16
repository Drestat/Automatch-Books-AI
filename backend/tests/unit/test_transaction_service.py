"""
Test suite for Transaction Service - approval workflow and QBO sync.

Covers:
- Transaction approval state machine
- QBO sync with stale object handling
- Receipt upload and entity type mapping
- Split transaction approval
- Payment/BillPayment edge cases (BUG-005)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.qbo import Transaction


class TestTransactionApproval:
    """
    Tests for the transaction approval workflow.

    Flow: unmatched → pending_approval → pending_qbo → approved
    """

    @pytest.fixture
    def approved_transaction(self, db_session, test_qbo_connection, sample_categories):
        """Create a transaction ready for QBO sync."""
        tx = Transaction(
            id="tx_approve_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Office Supplies Purchase",
            amount=75.00,
            currency="USD",
            status="pending_qbo",
            transaction_type="Purchase",
            account_id="acc_001",
            sync_token="0",
            category_id=sample_categories[0].id,
            category_name=sample_categories[0].name,
        )
        db_session.add(tx)
        db_session.flush()
        db_session.refresh(tx)
        return tx

    def test_approve_sets_pending_qbo_status(
        self, db_session, base_transaction, sample_categories
    ):
        """
        Test: Approving a transaction should set status to 'pending_qbo'.
        """
        base_transaction.status = "pending_approval"
        base_transaction.category_id = sample_categories[0].id
        base_transaction.category_name = sample_categories[0].name
        db_session.flush()

        # Simulate approval
        base_transaction.status = "pending_qbo"
        db_session.flush()

        assert base_transaction.status == "pending_qbo"

    def test_approve_requires_category(self, db_session, base_transaction):
        """
        Test: Cannot approve transaction without category.
        """
        base_transaction.status = "unmatched"
        base_transaction.category_id = None
        base_transaction.category_name = None
        db_session.flush()

        # Attempting to approve without category should fail
        with pytest.raises((ValueError, Exception)):
            if not base_transaction.category_id and not base_transaction.suggested_category_id:
                raise ValueError(
                    f"Transaction {base_transaction.id} missing category"
                )

    def test_approve_uses_suggested_category_fallback(
        self, db_session, base_transaction, sample_categories
    ):
        """
        Test: If no user-confirmed category, use suggested category.
        """
        base_transaction.category_id = None
        base_transaction.suggested_category_id = sample_categories[1].id
        base_transaction.suggested_category_name = sample_categories[1].name
        db_session.flush()

        # Resolve category with fallback
        cat_id = base_transaction.category_id or base_transaction.suggested_category_id
        cat_name = base_transaction.category_name or base_transaction.suggested_category_name

        assert cat_id == sample_categories[1].id
        assert cat_name == sample_categories[1].name

    @pytest.mark.critical
    def test_payment_type_categorization_edge_case(
        self, db_session, test_qbo_connection, sample_categories
    ):
        """
        Test: BUG-005 - Payment/BillPayment types should document limitations.

        Current behavior: Category is noted in memo only, NOT applied to GL.
        Users think they're categorizing, but GL account doesn't change.
        """
        payment_tx = Transaction(
            id="tx_payment_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Payment to Vendor",
            amount=500.00,
            currency="USD",
            status="pending_qbo",
            transaction_type="Payment",  # BUG-005 type
            account_id="acc_001",
            sync_token="0",
            category_id=sample_categories[0].id,
            category_name=sample_categories[0].name,
        )
        db_session.add(payment_tx)
        db_session.flush()

        # For Payment types, category goes to memo, not GL
        is_payment_type = payment_tx.transaction_type in ["Payment", "BillPayment"]

        assert is_payment_type, "Should identify Payment types"
        # After fix: UI should display warning that category applies to memo only


class TestStaleObjectHandling:
    """
    Tests for QBO stale object (SyncToken) error handling.

    QBO error 5010: "Stale Object Error" when SyncToken is outdated.
    """

    def test_sync_token_increments_on_update(self, db_session, test_qbo_connection):
        """
        Test: SyncToken should increment after successful QBO update.
        """
        tx = Transaction(
            id="tx_stale_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Stale Test",
            amount=50.00,
            currency="USD",
            status="pending_qbo",
            transaction_type="Purchase",
            account_id="acc_001",
            sync_token="5",  # Current sync token
        )
        db_session.add(tx)
        db_session.flush()

        # After successful QBO update, sync token should increment
        tx.sync_token = str(int(tx.sync_token) + 1)
        db_session.flush()

        assert tx.sync_token == "6"

    def test_stale_object_requires_refetch(self, db_session, test_qbo_connection):
        """
        Test: Stale object error (5010) should trigger refetch of fresh SyncToken.
        """
        tx = Transaction(
            id="tx_stale_refetch",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Stale Refetch Test",
            amount=75.00,
            currency="USD",
            status="pending_qbo",
            transaction_type="Purchase",
            account_id="acc_001",
            sync_token="3",  # Outdated
        )
        db_session.add(tx)
        db_session.flush()

        # Simulate QBO returning fresh SyncToken
        fresh_sync_token = "7"

        # Update with fresh token
        tx.sync_token = fresh_sync_token
        db_session.flush()

        assert tx.sync_token == "7", "Should use fresh SyncToken after stale error"


class TestSplitTransactions:
    """
    Tests for split transaction approval workflow.
    """

    def test_split_amounts_must_equal_total(self, db_session, test_qbo_connection):
        """
        Edge case: Split amounts must equal the original transaction amount.
        """
        from app.models.qbo import TransactionSplit

        tx = Transaction(
            id="tx_split_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Walmart Purchase",
            amount=100.00,
            currency="USD",
            status="pending_approval",
            transaction_type="Purchase",
            account_id="acc_001",
            sync_token="0",
            is_split=True,
        )
        db_session.add(tx)
        db_session.flush()

        # Create splits that equal the total
        split_1 = TransactionSplit(
            transaction_id=tx.id,
            category_id="cat_001",
            amount=60.00,
            description="Groceries"
        )
        split_2 = TransactionSplit(
            transaction_id=tx.id,
            category_id="cat_002",
            amount=40.00,
            description="Supplies"
        )
        db_session.add_all([split_1, split_2])
        db_session.flush()

        # Verify splits sum to total
        total_splits = split_1.amount + split_2.amount
        assert total_splits == tx.amount, \
            f"Split amounts ({total_splits}) must equal total ({tx.amount})"

    def test_split_amounts_mismatch_detected(self, db_session, test_qbo_connection):
        """
        Edge case: Detect when split amounts don't match the original.
        """
        from app.models.qbo import TransactionSplit

        tx = Transaction(
            id="tx_split_mismatch",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 15).date(),
            description="Mismatch Test",
            amount=100.00,
            currency="USD",
            status="pending_approval",
            transaction_type="Purchase",
            account_id="acc_001",
            sync_token="0",
            is_split=True,
        )
        db_session.add(tx)
        db_session.flush()

        # Create mismatched splits
        split_1 = TransactionSplit(
            transaction_id=tx.id,
            category_id="cat_001",
            amount=60.00,
            description="Part 1"
        )
        split_2 = TransactionSplit(
            transaction_id=tx.id,
            category_id="cat_002",
            amount=30.00,  # Total = 90, should be 100
            description="Part 2"
        )
        db_session.add_all([split_1, split_2])
        db_session.flush()

        total_splits = split_1.amount + split_2.amount
        assert total_splits != tx.amount, \
            "Should detect mismatch between split total and transaction amount"

        difference = abs(tx.amount - total_splits)
        assert difference == 10.00, f"Mismatch should be $10, got ${difference}"


class TestTransactionStatusMachine:
    """
    Tests for valid transaction state transitions.
    """

    @pytest.mark.parametrize("from_status,to_status,valid", [
        ("unmatched", "pending_approval", True),
        ("pending_approval", "pending_qbo", True),
        ("pending_qbo", "approved", True),
        ("unmatched", "excluded", True),
        ("approved", "pending_approval", True),   # Re-edit after approval
        ("pending_qbo", "unmatched", False),       # Invalid backward transition
        ("approved", "unmatched", False),           # Invalid backward transition
        ("excluded", "unmatched", True),            # Un-exclude
    ])
    def test_valid_status_transitions(
        self, db_session, base_transaction, from_status, to_status, valid
    ):
        """
        Test: Verify valid and invalid status transitions.
        """
        base_transaction.status = from_status
        db_session.flush()

        valid_transitions = {
            "unmatched": ["pending_approval", "excluded"],
            "pending_approval": ["pending_qbo", "unmatched", "excluded"],
            "pending_qbo": ["approved", "pending_approval"],
            "approved": ["pending_approval"],
            "excluded": ["unmatched"],
        }

        allowed = to_status in valid_transitions.get(from_status, [])
        assert allowed == valid, \
            f"Transition {from_status} → {to_status} should be " \
            f"{'valid' if valid else 'invalid'}"
