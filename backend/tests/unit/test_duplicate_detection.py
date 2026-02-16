"""
Test suite for duplicate transaction detection.

BUG-001: CRITICAL
Location: backend/app/services/sync_service.py:200-206
Issue: Duplicate detection is completely disabled in production code
Impact: Users may end up with duplicate transactions in QuickBooks

This test suite verifies that _check_duplicates() method works correctly
and will serve as regression tests when the feature is re-enabled.
"""

import pytest
from datetime import datetime, timedelta
from app.services.sync_service import SyncService
from app.models.qbo import Transaction


@pytest.mark.critical
class TestDuplicateDetection:
    """
    Tests for duplicate transaction detection logic.

    Coverage: 8 test cases
    - Exact duplicates
    - Fuzzy duplicates (near dates)
    - Non-duplicates (different amounts, realms, currencies)
    - Edge cases (negative amounts, zero amounts, multiple matches)
    """

    @pytest.mark.critical
    def test_exact_duplicate_same_amount_same_date(
        self, sync_service, db_session, base_transaction, test_qbo_connection
    ):
        """
        Test Case 1: Exact duplicate with same amount and same date.

        Expected: High confidence match (≥0.95)
        Status: Should be marked as potential_duplicate
        """
        # Create duplicate with different description
        duplicate = Transaction(
            id="tx_dup_001",
            realm_id=test_qbo_connection.realm_id,
            date=base_transaction.date,  # Same date
            description="Different Vendor Name",  # Description shouldn't matter
            amount=base_transaction.amount,  # Same amount
            currency="USD",
            transaction_type="Purchase",
            account_id=base_transaction.account_id,
            status="unmatched",
            sync_token="0"
        )
        db_session.add(duplicate)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(duplicate)

        # Assertions
        assert match_id == base_transaction.id, f"Should match base transaction, got {match_id}"
        assert confidence >= 0.95, f"Confidence should be ≥0.95 for exact match, got {confidence}"
        assert duplicate.status == "potential_duplicate", \
            "Status should be set to potential_duplicate"

    @pytest.mark.critical
    @pytest.mark.parametrize("days_offset", [1, 2, 3])
    def test_fuzzy_duplicate_same_amount_near_date(
        self, sync_service, db_session, base_transaction, test_qbo_connection, days_offset
    ):
        """
        Test Case 2: Fuzzy duplicate with same amount within ±3 day window.

        Expected: Medium-high confidence (0.70-0.95)
        Rationale: Transactions may appear with slight date variations
        """
        # Create transaction with offset date
        duplicate = Transaction(
            id=f"tx_fuzzy_{days_offset}",
            realm_id=test_qbo_connection.realm_id,
            date=base_transaction.date + timedelta(days=days_offset),  # Offset date
            description="Fuzzy Match Transaction",
            amount=base_transaction.amount,  # Same amount
            currency="USD",
            transaction_type="Purchase",
            account_id=base_transaction.account_id,
            status="unmatched",
            sync_token="0"
        )
        db_session.add(duplicate)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(duplicate)

        # Assertions
        assert match_id == base_transaction.id, \
            f"Should match base transaction for {days_offset}-day offset"
        assert 0.70 <= confidence < 0.95, \
            f"Confidence should be 0.70-0.95 for fuzzy match, got {confidence}"

    @pytest.mark.critical
    def test_no_duplicate_different_amount(
        self, sync_service, db_session, base_transaction, test_qbo_connection
    ):
        """
        Test Case 3: Different amount should NOT match.

        Expected: No match (None, None)
        Rationale: Amount is primary duplicate detection signal
        """
        # Create transaction with different amount
        different = Transaction(
            id="tx_diff_amount",
            realm_id=test_qbo_connection.realm_id,
            date=base_transaction.date,  # Same date
            description=base_transaction.description,  # Same description
            amount=base_transaction.amount + 50,  # Different amount
            currency="USD",
            transaction_type="Purchase",
            account_id=base_transaction.account_id,
            status="unmatched",
            sync_token="0"
        )
        db_session.add(different)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(different)

        # Assertions
        assert match_id is None, "Should NOT match transactions with different amounts"
        assert confidence is None, "Confidence should be None for non-matches"

    @pytest.mark.critical
    @pytest.mark.security
    def test_no_duplicate_different_realm(
        self, sync_service, db_session, base_transaction, test_qbo_connection
    ):
        """
        Test Case 4: Different realm should NOT match (security test).

        Expected: No match (None, None)
        Rationale: CRITICAL - Must prevent cross-realm data leakage
        """
        # Create transaction in different realm (potential security breach)
        malicious = Transaction(
            id="tx_cross_realm",
            realm_id="different_realm_id",  # Security: Different realm
            date=base_transaction.date,  # Same date
            description=base_transaction.description,  # Same description
            amount=base_transaction.amount,  # Same amount
            currency="USD",
            transaction_type="Purchase",
            account_id=base_transaction.account_id,
            status="unmatched",
            sync_token="0"
        )
        db_session.add(malicious)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(malicious)

        # Assertions
        assert match_id is None, \
            "SECURITY: Must NOT match transactions across different realms"
        assert confidence is None, "Confidence should be None for cross-realm attempts"

    @pytest.mark.critical
    def test_no_duplicate_different_currency(
        self, sync_service, db_session, base_transaction, test_qbo_connection
    ):
        """
        Test Case 5: Same amount, different currency should NOT match.

        Expected: No match (None, None)
        Rationale: $100 USD ≠ $100 CAD
        """
        # Create transaction with different currency
        different_currency = Transaction(
            id="tx_diff_currency",
            realm_id=test_qbo_connection.realm_id,
            date=base_transaction.date,  # Same date
            description="Same amount but CAD",
            amount=base_transaction.amount,  # Same numerical amount
            currency="CAD",  # Different currency
            transaction_type="Purchase",
            account_id=base_transaction.account_id,
            status="unmatched",
            sync_token="0"
        )
        db_session.add(different_currency)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(different_currency)

        # Assertions
        assert match_id is None, "Should NOT match transactions with different currencies"
        assert confidence is None, "Confidence should be None for currency mismatches"

    @pytest.mark.critical
    def test_negative_amounts_refunds(
        self, sync_service, db_session, test_qbo_connection
    ):
        """
        Test Case 6: Negative amounts (refunds) should be detected as duplicates.

        Expected: Match detected with high confidence
        Rationale: Refunds can also be duplicated
        """
        # Create original refund
        original_refund = Transaction(
            id="tx_refund_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 2, 1).date(),
            description="Refund Transaction",
            amount=-50.00,  # Negative amount
            currency="USD",
            transaction_type="Refund",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(original_refund)
        db_session.flush()

        # Create duplicate refund
        duplicate_refund = Transaction(
            id="tx_refund_dup",
            realm_id=test_qbo_connection.realm_id,
            date=original_refund.date,
            description="Duplicate Refund",
            amount=-50.00,  # Same negative amount
            currency="USD",
            transaction_type="Refund",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(duplicate_refund)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(duplicate_refund)

        # Assertions
        assert match_id == original_refund.id, "Refunds should be detected as duplicates"
        assert confidence >= 0.95, "Refund duplicates should have high confidence"

    @pytest.mark.critical
    def test_zero_amount_transactions(
        self, sync_service, db_session, test_qbo_connection
    ):
        """
        Test Case 7: Zero amount transactions should NOT trigger false duplicates.

        Expected: No match (or low confidence)
        Rationale: $0 transactions are common for adjustments/corrections
        """
        # Create original zero-amount transaction
        zero_tx_1 = Transaction(
            id="tx_zero_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 2, 5).date(),
            description="Zero Amount Adjustment",
            amount=0.00,  # Zero amount
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(zero_tx_1)
        db_session.flush()

        # Create another zero-amount transaction
        zero_tx_2 = Transaction(
            id="tx_zero_002",
            realm_id=test_qbo_connection.realm_id,
            date=zero_tx_1.date,
            description="Different Zero Adjustment",
            amount=0.00,  # Zero amount
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(zero_tx_2)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(zero_tx_2)

        # Zero-amount transactions should either:
        # 1. Not match (preferred)
        # 2. Have low confidence (<0.50)
        if match_id:
            assert confidence < 0.50, \
                "Zero amount duplicates should have low confidence to avoid false positives"
        # Else: No match is acceptable behavior

    @pytest.mark.critical
    def test_multiple_potential_duplicates_returns_highest_confidence(
        self, sync_service, db_session, test_qbo_connection
    ):
        """
        Test Case 8: When multiple potential duplicates exist, return highest confidence.

        Expected: Returns the best match (highest confidence)
        Rationale: Helps user resolve ambiguity
        """
        base_date = datetime(2024, 3, 1).date()
        base_amount = 250.00

        # Create original transaction
        original = Transaction(
            id="tx_multi_base",
            realm_id=test_qbo_connection.realm_id,
            date=base_date,
            description="Original Transaction",
            amount=base_amount,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(original)

        # Create fuzzy match (lower confidence)
        fuzzy_match = Transaction(
            id="tx_multi_fuzzy",
            realm_id=test_qbo_connection.realm_id,
            date=base_date + timedelta(days=2),  # 2 days off
            description="Fuzzy Match",
            amount=base_amount,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(fuzzy_match)
        db_session.flush()

        # Create new transaction that could match both
        new_transaction = Transaction(
            id="tx_multi_new",
            realm_id=test_qbo_connection.realm_id,
            date=base_date,  # Exact match with original
            description="Potential Duplicate",
            amount=base_amount,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(new_transaction)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(new_transaction)

        # Should match the original (exact date) over fuzzy match
        assert match_id == original.id, \
            "Should return highest confidence match (original with exact date)"
        assert confidence >= 0.95, "Should have high confidence for exact match"


@pytest.mark.critical
class TestDuplicateDetectionEdgeCases:
    """
    Additional edge case tests for duplicate detection.
    """

    def test_date_boundary_year_end(
        self, sync_service, db_session, test_qbo_connection
    ):
        """
        Edge case: Transactions at year boundary (Dec 31 vs Jan 1).

        Expected: Should detect as fuzzy duplicate if within window
        """
        # Transaction on Dec 31
        dec_tx = Transaction(
            id="tx_dec_31",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2023, 12, 31).date(),
            description="Year End Transaction",
            amount=500.00,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(dec_tx)
        db_session.flush()

        # Transaction on Jan 2 (2 days later, different year)
        jan_tx = Transaction(
            id="tx_jan_02",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 1, 2).date(),
            description="New Year Transaction",
            amount=500.00,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(jan_tx)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(jan_tx)

        # Should still detect as duplicate despite year boundary
        assert match_id == dec_tx.id, "Should detect duplicates across year boundary"
        assert 0.70 <= confidence < 0.95, "Should have medium-high confidence"

    def test_very_large_amounts(
        self, sync_service, db_session, test_qbo_connection
    ):
        """
        Edge case: Very large transaction amounts (>$1M).

        Expected: Should still detect duplicates accurately
        """
        large_amount = 1_500_000.00

        # Original large transaction
        large_tx = Transaction(
            id="tx_large_001",
            realm_id=test_qbo_connection.realm_id,
            date=datetime(2024, 4, 1).date(),
            description="Large Transaction",
            amount=large_amount,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(large_tx)
        db_session.flush()

        # Duplicate large transaction
        large_tx_dup = Transaction(
            id="tx_large_002",
            realm_id=test_qbo_connection.realm_id,
            date=large_tx.date,
            description="Duplicate Large Transaction",
            amount=large_amount,
            currency="USD",
            transaction_type="Purchase",
            account_id="acc_001",
            status="unmatched",
            sync_token="0"
        )
        db_session.add(large_tx_dup)
        db_session.flush()

        # Check for duplicates
        match_id, confidence = sync_service._check_duplicates(large_tx_dup)

        # Should detect duplicates even for large amounts
        assert match_id == large_tx.id, "Should detect duplicates for large amounts"
        assert confidence >= 0.95, "Should have high confidence"
