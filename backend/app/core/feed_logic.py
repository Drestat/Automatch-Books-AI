from typing import Dict, Any, Tuple

class FeedLogic:
    """
    Pure logic engine for determining if a QBO transaction should appear 
    in the 'Categorized' tab or the 'For Review' tab, explicitly mirroring 
    QBO's Banking Feed behavior.
    """

    @staticmethod
    def analyze(transaction_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Analyzes a raw QBO transaction JSON and determines its categorization status.
        
        Returns:
            Tuple[bool, str]: (is_qbo_matched, reason)
            - is_qbo_matched: True if 'Categorized', False if 'For Review'
            - reason: A human-readable explanation of the decision logic
        """
        
        # 1. Extract Signals
        txn_type = FeedLogic._get_txn_type(transaction_data)
        doc_number = transaction_data.get("DocNumber")
        sync_token = int(transaction_data.get("SyncToken", "0"))
        has_linked_txn = FeedLogic._has_linked_txn(transaction_data)
        has_doc_number = bool(doc_number)
        
        # 2. Determine Entity Category
        is_bill_payment = FeedLogic._is_bill_payment(transaction_data)
        is_manual_entry = txn_type == "54"
        is_bank_feed = not is_manual_entry and not is_bill_payment
        
        # 3. Apply Heuristics
        
        # CASE A: BILL PAYMENTS
        # BillPayments in the Banking Feed are part of QBO's payment matching workflow.
        # Even with LinkedTxn to a Bill, they show as "match suggestions" until user confirms.
        # Since we cannot detect user confirmation via API, treat all BillPayments as For Review.
        if is_bill_payment:
            return False, "BillPayment (Requires User Confirmation in Banking Feed)"
                
        # CASE B: MANUAL ENTRIES (TxnType 54)
        # Distinguish between user creation (Categorized) and QBO Match Suggestions (For Review)
        if is_manual_entry:
            if has_linked_txn:
                 return True, "Manual Entry with LinkedTxn (Matched)"
            
            # The "Law of Freshness": SyncToken 0 means freshly created by user -> Categorized
            if sync_token == 0:
                # We assume if the user just created it, they consider it done.
                return True, "Fresh Manual Entry (SyncToken 0) - Assumed Finalized"
            
            # The "Law of Modification": SyncToken > 0 means touched by QBO -> For Review
            # Often implies a 'Match Suggestion' was attached or it's waiting for approval
            return False, "Modified Manual Entry (SyncToken > 0) - Assumed Pending Match"
            
        # CASE C: BANK FEED IMPORTS (TxnType 1, 11, etc)
        # The standard flow. Needs explicit confirmation to be categorized.
        if has_linked_txn:
            return True, "Bank Feed with LinkedTxn (Matched)"
        
        if has_doc_number:
            return True, "Bank Feed with DocNumber (User Finalized)"
            
        return False, "Bank Feed Suggestion (No Link, No DocNumber)"

    @staticmethod
    def _get_txn_type(data: Dict[str, Any]) -> str:
        """Extracts TxnType from PurchaseEx or top-level fields."""
        # Try finding in PurchaseEx
        purchase_ex = data.get("PurchaseEx", {})
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    return item.get("value", {}).get("Value")
        return "1" # Default to Bank Feed Import if unknown

    @staticmethod
    def _has_linked_txn(data: Dict[str, Any]) -> bool:
        """Checks recursively for any LinkedTxn in Line items."""
        for line in data.get("Line", []):
            if "LinkedTxn" in line and line["LinkedTxn"]:
                return True
        return False

    @staticmethod
    def _is_bill_payment(data: Dict[str, Any]) -> bool:
        """Identifying BillPayment structure."""
        return "VendorRef" in data and ("CheckPayment" in data or "CreditCardPayment" in data)
