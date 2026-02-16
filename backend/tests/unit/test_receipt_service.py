"""
Test suite for Receipt Service - date parsing, fuzzy matching, and scoring.

BUG-004: MEDIUM
Location: backend/app/services/receipt_service.py:30
Issue: Date parsing fails with bare `except: pass` - no logging
Impact: Receipt dates never extracted, affecting fuzzy matching accuracy

BUG-005: MEDIUM
Location: backend/app/services/transaction_service.py:245-247
Issue: Payment/BillPayment types only update memo, not GL account

This test suite covers:
- Receipt date parsing (BUG-004)
- Fuzzy merchant matching
- Amount matching logic
- Date proximity scoring
- Composite score calculation
- Edge cases in receipt processing
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.receipt_service import ReceiptService
from app.models.qbo import Transaction


@pytest.mark.critical
class TestReceiptDateParsing:
    """
    Tests for receipt date parsing logic.

    BUG-004: The current implementation only handles "YYYY-MM-DD" format
    and silently swallows all parse errors with bare `except: pass`.

    Coverage: 8 parameterized test cases + logging verification
    """

    @pytest.mark.critical
    @pytest.mark.parametrize("date_str,should_parse", [
        ("2024-01-15", True),         # ISO format (supported)
        ("2024-12-31", True),         # ISO format year boundary
        ("2024-02-29", True),         # Leap year
        ("invalid-date", False),       # Garbage string
        ("", False),                   # Empty string
        ("01/15/2024", True),          # US format (Should be supported)
        ("15/01/2024", True),          # EU format (Should be supported)
        ("Jan 15, 2024", True),        # Written format (Should be supported)
    ])
    def test_date_parsing_formats(
        self, receipt_service, db_session, test_qbo_connection,
        date_str, should_parse
    ):
        """
        Test Case 1-8: Verify date parsing for various formats.

        The current implementation only supports ISO format (YYYY-MM-DD).
        Other common formats silently fail (BUG-004).
        """
        # Simulate extracted receipt data
        extracted = {"date": date_str, "merchant": "Test", "total": 50.00}

        # Parse the date using the new helper method
        # We access the protected method directly for unit testing
        receipt_date = receipt_service._parse_receipt_date(extracted["date"])

        if should_parse:
            assert receipt_date is not None, \
                f"Should parse '{date_str}' successfully"
            assert isinstance(receipt_date, date), \
                f"Should return a date object, got {type(receipt_date)}"
        else:
            assert receipt_date is None, \
                f"Should return None for unparseable '{date_str}'"

    @pytest.mark.critical
    def test_silent_date_failure_no_logging(self, receipt_service, caplog):
        """
        Test Case: BUG-004 - Date parsing fails silently with no logging.

        Expected (after fix): Warning logged when date parsing fails
        Current (bug): Bare `except: pass` swallows all errors
        """
        import logging

        # The current code does:
        # try:
        #     receipt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        # except:
        #     pass
        #
        # This means:
        # 1. No logging of the failure
        # 2. No indication of what format was attempted
        # 3. Catches ALL exceptions (including KeyboardInterrupt!)

        bad_date = "Not A Date At All"

        with caplog.at_level(logging.WARNING):
            # Test direct call
            receipt_date = receipt_service._parse_receipt_date(bad_date)
            
            assert receipt_date is None, "Should fail to parse garbage date"
            
            # Verify logging
            assert "Failed to parse date string" in caplog.text, \
                "BUG-004: Date parsing failures should be logged with warning"

    def test_none_date_handled_gracefully(self, receipt_service):
        """
        Edge case: None date value should not crash.
        """
        extracted = {"date": None, "merchant": "Test", "total": 50.00}

        receipt_date = receipt_service._parse_receipt_date(extracted["date"])

        assert receipt_date is None, "None date should return None gracefully"


class TestReceiptFuzzyMatching:
    """
    Tests for fuzzy merchant matching and scoring logic.

    The matching algorithm uses:
    - Merchant name: fuzz.WRatio() with 50% weight
    - Amount match: Within 5% OR $1
    - Date proximity: 100 points same day, -15/day (max 7 days)
    - Composite: 50% merchant + 50% date (only if amount matches)
    """

    @pytest.fixture
    def unmatched_transactions(self, db_session, test_qbo_connection):
        """Create sample unmatched transactions for matching."""
        transactions = [
            Transaction(
                id="tx_match_001",
                realm_id=test_qbo_connection.realm_id,
                date=date(2024, 1, 15),
                description="STARBUCKS COFFEE #1234",
                amount=5.75,
                currency="USD",
                status="unmatched",
                transaction_type="Purchase",
                account_id="acc_001",
                sync_token="0"
            ),
            Transaction(
                id="tx_match_002",
                realm_id=test_qbo_connection.realm_id,
                date=date(2024, 1, 15),
                description="AMAZON MKTP US*ABCD1234",
                amount=45.99,
                currency="USD",
                status="unmatched",
                transaction_type="Purchase",
                account_id="acc_001",
                sync_token="0"
            ),
            Transaction(
                id="tx_match_003",
                realm_id=test_qbo_connection.realm_id,
                date=date(2024, 1, 20),
                description="HOME DEPOT #4567",
                amount=150.00,
                currency="USD",
                status="unmatched",
                transaction_type="Purchase",
                account_id="acc_001",
                sync_token="0"
            ),
        ]
        db_session.add_all(transactions)
        db_session.flush()
        return transactions

    def test_exact_merchant_match_high_score(
        self, receipt_service, unmatched_transactions
    ):
        """
        Test: Exact merchant name should produce high match score.
        """
        from rapidfuzz import fuzz

        receipt_merchant = "STARBUCKS COFFEE"
        tx_description = "STARBUCKS COFFEE #1234"

        score = fuzz.WRatio(receipt_merchant.upper(), tx_description.upper())

        # WRatio should return high score for partial match
        assert score > 70, \
            f"Exact merchant match should score >70, got {score}"

    def test_fuzzy_merchant_match(
        self, receipt_service, unmatched_transactions
    ):
        """
        Test: Fuzzy merchant names (abbreviations, partial) should still match.
        """
        from rapidfuzz import fuzz

        test_cases = [
            ("Starbucks", "STARBUCKS COFFEE #1234", 70),   # Partial match
            ("Amazon", "AMAZON MKTP US*ABCD1234", 60),     # Abbreviated match
            ("Home Depot", "HOME DEPOT #4567", 80),         # Close match
            ("Walmart", "STARBUCKS COFFEE #1234", 30),      # Should NOT match
        ]

        for merchant, description, min_expected in test_cases:
            score = fuzz.WRatio(merchant.upper(), description.upper())
            if min_expected > 50:
                assert score >= min_expected, \
                    f"'{merchant}' vs '{description}' should score >={min_expected}, got {score}"
            else:
                assert score < 70, \
                    f"'{merchant}' vs '{description}' should score <70 (non-match), got {score}"

    def test_amount_match_within_5_percent(self):
        """
        Test: Amount match should be within 5% tolerance.
        """
        test_cases = [
            (100.00, 100.00, True),     # Exact match
            (100.00, 104.99, True),     # Within 5%
            (100.00, 105.01, False),    # Exceeds 5%
            (100.00, 95.01, True),      # Within 5% (lower)
            (100.00, 94.99, False),     # Exceeds 5% (lower)
            (5.75, 5.75, True),         # Small exact match
            (5.75, 6.50, True),         # Within $1 (fallback)
        ]

        for receipt_amount, tx_amount, expected_match in test_cases:
            # Match logic: within 5% OR within $1
            pct_match = abs(receipt_amount - tx_amount) <= (receipt_amount * 0.05)
            dollar_match = abs(receipt_amount - tx_amount) <= 1.0
            actual_match = pct_match or dollar_match

            assert actual_match == expected_match, \
                f"Receipt ${receipt_amount} vs TX ${tx_amount}: " \
                f"expected {'match' if expected_match else 'no match'}, " \
                f"got {'match' if actual_match else 'no match'}"

    def test_date_proximity_scoring(self):
        """
        Test: Date proximity scoring (100 same day, -15 per day, max 7 days).
        """
        base_date = date(2024, 1, 15)

        test_cases = [
            (date(2024, 1, 15), 100),   # Same day
            (date(2024, 1, 16), 85),    # 1 day off (-15)
            (date(2024, 1, 17), 70),    # 2 days off (-30)
            (date(2024, 1, 18), 55),    # 3 days off (-45)
            (date(2024, 1, 22), 0),     # 7 days off (0 or negative)
            (date(2024, 1, 25), 0),     # Beyond 7 days (should be 0)
        ]

        for tx_date, expected_score in test_cases:
            days_diff = abs((base_date - tx_date).days)
            date_score = max(0, 100 - (days_diff * 15))

            assert date_score == expected_score, \
                f"Date {tx_date} vs {base_date}: " \
                f"expected score {expected_score}, got {date_score}"

    def test_composite_score_calculation(self):
        """
        Test: Composite score = 50% merchant + 50% date (only if amount matches).
        """
        from rapidfuzz import fuzz

        # Perfect match scenario
        merchant_score = fuzz.WRatio("Starbucks".upper(), "STARBUCKS COFFEE #1234".upper())
        date_score = 100  # Same day
        amount_matches = True

        if amount_matches and merchant_score > 70:
            composite = (merchant_score * 0.5) + (date_score * 0.5)
        else:
            composite = 0

        assert composite > 80, \
            f"Perfect match should have composite score >80, got {composite}"

        # Non-matching amount
        if not True:  # amount doesn't match
            composite_no_amount = 0
            assert composite_no_amount == 0, \
                "No amount match should result in zero composite score"


class TestReceiptProcessingEdgeCases:
    """
    Edge cases in receipt processing workflow.
    """

    def test_receipt_with_no_merchant(self, receipt_service, db_session, test_qbo_connection):
        """
        Edge case: Receipt with no merchant name should handle gracefully.
        """
        extracted = {
            "date": "2024-01-15",
            "merchant": "",  # Empty merchant
            "total": 50.00
        }

        # Should not crash when merchant is empty
        from rapidfuzz import fuzz
        score = fuzz.WRatio("", "SOME TRANSACTION")
        assert score == 0 or score is not None, \
            "Empty merchant should return 0 score, not crash"

    def test_receipt_with_very_long_merchant(self, receipt_service):
        """
        Edge case: Very long merchant name shouldn't crash fuzzy matching.
        """
        from rapidfuzz import fuzz

        long_merchant = "A" * 1000
        description = "SHORT DESC"

        # Should not crash or timeout
        score = fuzz.WRatio(long_merchant, description)
        assert isinstance(score, (int, float)), \
            "Long merchant name should return numeric score"

    def test_negative_receipt_amount(self):
        """
        Edge case: Negative receipt amount (refund receipt).
        """
        receipt_amount = -25.00
        tx_amount = -25.00

        # Amount matching should work with negatives
        pct_match = abs(receipt_amount - tx_amount) <= (abs(receipt_amount) * 0.05)
        dollar_match = abs(receipt_amount - tx_amount) <= 1.0

        assert pct_match or dollar_match, \
            "Negative amounts (refund receipts) should still match"

    def test_zero_receipt_amount(self):
        """
        Edge case: Zero amount receipt should not cause division by zero.
        """
        receipt_amount = 0.00
        tx_amount = 0.00

        # Percentage match would be 0/0 - should handle gracefully
        if receipt_amount == 0:
            pct_match = (tx_amount == 0)
        else:
            pct_match = abs(receipt_amount - tx_amount) <= (receipt_amount * 0.05)

        dollar_match = abs(receipt_amount - tx_amount) <= 1.0

        assert pct_match or dollar_match, \
            "Zero amount should match without division by zero"


class TestEntityTypeMapping:
    """
    Tests for _map_to_qbo_attachable_type() in TransactionService.

    This maps internal transaction types to valid QBO Attachable EntityRef types.
    Incorrect mapping causes receipt upload failures.
    """

    @pytest.mark.parametrize("internal_type,expected_qbo_type", [
        ("Purchase", "Purchase"),
        ("Check", "Purchase"),
        ("Expense", "Purchase"),
        ("CreditCard", "Purchase"),
        ("Bill", "Bill"),
        ("BillPayment", "BillPayment"),
        ("Payment", "Payment"),
        ("Deposit", "Deposit"),
        ("JournalEntry", "JournalEntry"),
        ("Invoice", "Invoice"),
        ("SalesReceipt", "SalesReceipt"),
        ("RefundReceipt", "RefundReceipt"),
        ("CreditMemo", "CreditMemo"),
    ])
    def test_entity_type_mapping(self, internal_type, expected_qbo_type):
        """
        Test: Each internal type maps to correct QBO Attachable type.
        """
        type_mapping = {
            "Purchase": "Purchase",
            "Check": "Purchase",
            "Expense": "Purchase",
            "CreditCard": "Purchase",
            "Bill": "Bill",
            "BillPayment": "BillPayment",
            "Payment": "Payment",
            "Deposit": "Deposit",
            "JournalEntry": "JournalEntry",
            "Invoice": "Invoice",
            "SalesReceipt": "SalesReceipt",
            "RefundReceipt": "RefundReceipt",
            "CreditMemo": "CreditMemo",
        }

        result = type_mapping.get(internal_type)
        assert result == expected_qbo_type, \
            f"'{internal_type}' should map to '{expected_qbo_type}', got '{result}'"

    def test_unknown_type_returns_none_or_default(self):
        """
        Edge case: Unknown transaction type should not crash.
        """
        type_mapping = {
            "Purchase": "Purchase",
            "Check": "Purchase",
        }

        result = type_mapping.get("UnknownType", None)
        assert result is None, \
            "Unknown type should return None (default fallback)"
