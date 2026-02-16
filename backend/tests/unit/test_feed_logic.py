import unittest
from app.core.feed_logic import FeedLogic

class TestFeedLogic(unittest.TestCase):
    
    def test_lara_lamination_fresh_manual(self):
        """
        Lara's Lamination: Manual Entry (54), SyncToken 0 (Fresh).
        Should be CATEGORIZED.
        """
        data = {
            "PurchaseEx": {"any": [{"value": {"Name": "TxnType", "Value": "54"}}]},
            "SyncToken": "0",
            "Line": [{"AccountBasedExpenseLineDetail": {"AccountRef": {"name": "Office Supplies"}}}],
            "EntityRef": {"name": "Lara Lamination"},
            "ClrStatus": "R",
            "DocNumber": None
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertTrue(matched, f"Lara should be Categorized. Reason: {reason}")
        self.assertIn("Categorized Manual Entry", reason)

    def test_tania_nursery_modified_manual(self):
        """
        Tania's Nursery: Manual Entry (54), SyncToken 1 (Modified).
        Should be FOR REVIEW (Pending Match Suggestion).
        """
        data = {
            "PurchaseEx": {"any": [{"value": {"Name": "TxnType", "Value": "54"}}]},
            "SyncToken": "1",
            "Line": [],
            "DocNumber": "50",
            "ClrStatus": "Create"
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertFalse(matched, f"Tania should be For Review. Reason: {reason}")
        self.assertIn("Unreconciled Manual Entry", reason)

    def test_norton_lumber_bill_payment_linked(self):
        """
        Norton Lumber: BillPayment, Linked to Bill.
        Should be FOR REVIEW (BillPayments are part of matching workflow).
        """
        data = {
            "VendorRef": {"value": "123"},
            "CreditCardPayment": {},
            "Line": [{"LinkedTxn": [{"TxnId": "25", "TxnType": "Bill"}]}],
            "SyncToken": "0"
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertFalse(matched, f"BillPayment should be For Review. Reason: {reason}")
        self.assertIn("BillPayment", reason)

    def test_norton_lumber_bill_payment_unlinked(self):
        """
        Norton Lumber (Hypothetical): BillPayment, NO Link.
        Should be FOR REVIEW.
        """
        data = {
            "VendorRef": {"value": "123"},
            "CreditCardPayment": {},
            "Line": [],
            "SyncToken": "0"
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertFalse(matched, f"Unlinked BillPayment should be For Review. Reason: {reason}")
        self.assertIn("BillPayment", reason)

    def test_bobs_burger_bank_feed_suggestion(self):
        """
        Bob's Burger: Standard Bank Feed (1), No Link, No Doc.
        Should be FOR REVIEW.
        """
        data = {
            "PurchaseEx": {"any": [{"value": {"Name": "TxnType", "Value": "1"}}]},
            "Line": [],
            "EntityRef": {"name": "Bob's Burgers"},
            "DocNumber": None,
            "SyncToken": "0"
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertFalse(matched, f"Bank Feed Suggestion should be For Review. Reason: {reason}")
        self.assertIn("Missing Specific Category", reason)

    def test_bank_feed_finalized(self):
        """
        Standard Bank Feed (1) with DocNumber.
        Should be CATEGORIZED.
        """
        data = {
            "PurchaseEx": {"any": [{"value": {"Name": "TxnType", "Value": "1"}}]},
            "Line": [{"AccountBasedExpenseLineDetail": {"AccountRef": {"name": "Meals & Entertainment"}}}],
            "EntityRef": {"name": "Bob's Burgers"},
            "DocNumber": "101",
            "SyncToken": "0"
        }
        matched, reason = FeedLogic.analyze(data)
        self.assertTrue(matched, f"Finalized Bank Feed should be Categorized. Reason: {reason}")

if __name__ == "__main__":
    unittest.main()
