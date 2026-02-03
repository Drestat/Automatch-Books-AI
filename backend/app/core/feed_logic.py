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
            # LinkedTxn means QBO has suggested a match -> For Review
            if has_linked_txn:
                 return False, "Manual Entry with LinkedTxn (Match Suggestion)"
            
            # Check if transaction has a specific category (not Uncategorized)
            has_specific_category = FeedLogic._has_specific_category(transaction_data)
            
            # If user set a specific category, it's finalized -> Categorized
            # This handles cases like "Books By Bessie" with "Sales of Product Income"
            if has_specific_category:
                return True, "Manual Entry with Specific Category (User Finalized)"
            
            # The "Law of Freshness": SyncToken 0 means freshly created by user -> Categorized
            if sync_token == 0:
                # We assume if the user just created it, they consider it done.
                return True, "Fresh Manual Entry (SyncToken 0) - Assumed Finalized"
            
            # The "Law of Modification": SyncToken > 0 with no category means touched by QBO -> For Review
            # Often implies a 'Match Suggestion' was attached or it's waiting for approval
            return False, "Modified Manual Entry (SyncToken > 0, No Category) - Assumed Pending Match"
            
        # CASE C: BANK FEED IMPORTS (TxnType 1, 11, etc)
        # The standard flow. Needs explicit confirmation to be categorized.
        # LinkedTxn means QBO has suggested a match -> For Review
        if has_linked_txn:
            return False, "Bank Feed with LinkedTxn (Match Suggestion)"
        
        # DocNumber means user has explicitly finalized -> Categorized
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

    @staticmethod
    def _has_specific_category(data: Dict[str, Any]) -> bool:
        """
        Checks if transaction has a specific category (not Uncategorized or Ask My Accountant).
        This indicates the user has finalized the categorization.
        """
        # Check all Line items for category information
        for line in data.get("Line", []):
            # Check various detail types for AccountRef
            detail = None
            if "AccountBasedExpenseLineDetail" in line:
                detail = line["AccountBasedExpenseLineDetail"]
            elif "JournalEntryLineDetail" in line:
                detail = line["JournalEntryLineDetail"]
            elif "DepositLineDetail" in line:
                detail = line["DepositLineDetail"]
            elif "SalesItemLineDetail" in line:
                detail = line["SalesItemLineDetail"]
            elif "ItemBasedExpenseLineDetail" in line:
                detail = line["ItemBasedExpenseLineDetail"]
            
            if detail and "AccountRef" in detail:
                category_name = detail["AccountRef"].get("name", "").lower()
                # Check if it's a specific category (not generic)
                if category_name and "uncategorized" not in category_name and "ask my accountant" not in category_name:
                    return True
            
            # Also check ItemRef for item-based categorization
            if detail and "ItemRef" in detail:
                item_name = detail["ItemRef"].get("name", "").lower()
                if item_name and "uncategorized" not in item_name:
                    return True
        
        return False
