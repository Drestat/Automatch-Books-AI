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
        
        # 0. Check for Persistent Marker (#Accepted) in Note or Memo
        note = transaction_data.get("PrivateNote", "")
        memo = transaction_data.get("Memo", "")
        if "#Accepted" in note or "#Accepted" in memo:
            return True, "Categorized (Found #Accepted marker)"

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
        # USER REQUEST: Even recorded Bill Payments should be reviewed to verify the match.
        if is_bill_payment:
            return False, "BillPayment (User Verified Review Required)"
                
        # CASE B: MANUAL ENTRIES (TxnType 54, 3, etc)
        if is_manual_entry or txn_type == "3": # Include Checks (Type 3) as Manual
            # LinkedTxn means QBO has matched it -> Categorized (Matched)
            if has_linked_txn:
                 return False, "Manual Entry with LinkedTxn (Auto-Match Review)"
            
            # Check if transaction has a specific category
            has_specific_category = FeedLogic._has_specific_category(transaction_data)
            
            # Check ClrStatus
            # Unreconciled Manual Entries should be For Review!
            # User Feedback suggests Pam Seitz (Type 54) showing as Categorized is WRONG ("Broke").
            clr_status = FeedLogic._get_clr_status(transaction_data)
            if clr_status != "R":
                 return False, f"Unreconciled Manual Entry (Clr: {clr_status})"

            if has_specific_category and FeedLogic._has_payee(transaction_data):
                return True, "Categorized Manual Entry (Category + Payee)"
            
            if sync_token == 0:
                return True, "Fresh Manual Entry (SyncToken 0)"
            
            return False, "Modified Manual Entry (No Category)"
            
        # CASE C: BANK FEED IMPORTS (TxnType 1, 11, etc)
        
        if has_linked_txn:
            return False, "Auto-Match Suggestion (Needs User Verification)"

        # Check for QBO-side Suggestions (Type 1 with Category but NOT Cleared/Reconciled)
        clr_status = FeedLogic._get_clr_status(transaction_data)
        
        # EXCEPTION: Deposits (Books by Bessie)
        # If it's a Deposit (positive amount or DepositLineDetail) with a valid category, treat as Categorized?
        # Detecting Deposit via Structure (DepositLineDetail)
        is_deposit = False
        for line in transaction_data.get("Line", []):
            if "DepositLineDetail" in line:
                is_deposit = True
                break
        
        # If it's a Deposit with a Category/Payee, let it pass as Categorized even if Uncleared
        has_specific_category = FeedLogic._has_specific_category(transaction_data)
        has_payee = FeedLogic._has_payee(transaction_data)

        if is_deposit and has_specific_category and has_payee:
             return True, "Categorized Deposit (Category + Entity)"

        # Standard Type 1 Check (CreditCardCharge/Expense)
        # If it has a specific category AND a payee, we treat it as "Categorized".
        # Even if it is uncleared ('Create'), the presence of a specific category 
        # (not Uncategorized) and a Payee implies it has been processed or manually entered.
        if has_specific_category and has_payee:
             return True, "Categorized (Category + Payee)"
        
        if not has_specific_category:
            return False, "Missing Specific Category"
        
        if not has_payee:
            return False, "Missing Payee"

        return True, "Categorized (Category + Payee)"

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
    def _has_payee(data: Dict[str, Any]) -> bool:
        """
        Checks if transaction has a valid payee/vendor.
        Returns True if EntityRef (vendor/customer) exists.
        """
        # Check top-level EntityRef
        if "EntityRef" in data and data["EntityRef"].get("name"):
            return True
        
        # Check VendorRef
        if "VendorRef" in data and data["VendorRef"].get("name"):
            return True
        
        # Check CustomerRef
        if "CustomerRef" in data and data["CustomerRef"].get("name"):
            return True
        
        # Check Line-level entities (for Deposits/JournalEntries)
        for line in data.get("Line", []):
            for detail_key in ["DepositLineDetail", "JournalEntryLineDetail", "AccountBasedExpenseLineDetail"]:
                if detail_key in line:
                    detail = line[detail_key]
                    if "Entity" in detail and detail["Entity"].get("name"):
                        return True
        
        return False

    @staticmethod
    def _get_clr_status(data: Dict[str, Any]) -> str:
        """
        Extracts ClrStatus (Clearance Status) from transaction.
        Common values: 'R' (Reconciled), 'C' (Cleared), or None/Empty.
        Usually located in the Line matching the Bank Account.
        """
        # 1. Check Top Level (some tx objects have it)
        if "ClrStatus" in data:
            return data["ClrStatus"]
            
        # 2. Check Line Items
        for line in data.get("Line", []):
            # We look for the line that represents the Bank/CreditCard account.
            # Often it's hidden in QBO JSON, but sometimes exposed.
            if "ClrStatus" in line:
                return line["ClrStatus"]
                
        # 3. Default to "Create" (Uncleared) if not found
        return "Create"

    @staticmethod
    def _has_specific_category(data: Dict[str, Any]) -> bool:
        """
        Checks if transaction has a specific category (not Uncategorized, Ask My Accountant, or Opening Balance).
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
                # Added 'opening balance equity' as it often indicates an auto-generated setup txn needing review
                bad_keywords = ["uncategorized", "ask my accountant", "opening balance equity"]
                if category_name and not any(k in category_name for k in bad_keywords):
                    return True
            
            # Also check ItemRef for item-based categorization
            if detail and "ItemRef" in detail:
                item_name = detail["ItemRef"].get("name", "").lower()
                if item_name and "uncategorized" not in item_name:
                    return True
        
        return False
