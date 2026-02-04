
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.feed_logic import FeedLogic

def test_pam_seitz_logic():
    # Simulated Pam Seitz transaction data (Manual Entry Type 54, Uncleared)
    pam_data = {
        "PurchaseEx": {
            "any": [
                {
                    "value": {
                        "Name": "TxnType",
                        "Value": "54"
                    }
                }
            ]
        },
        "EntityRef": {
            "name": "Pam Seitz"
        },
        "Line": [
            {
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {
                        "name": "Legal & Professional Fees"
                    }
                }
            }
        ],
        "ClrStatus": "Create" # Uncleared
    }

    print("Testing Pam Seitz (Manual Entry, Uncleared)...")
    is_matched, reason = FeedLogic.analyze(pam_data)
    print(f"Result: is_matched={is_matched}, reason='{reason}'")
    
    assert is_matched == False, f"Expected False, got {is_matched}"
    assert "Unreconciled Manual Entry" in reason, f"Unexpected reason: {reason}"
    print("✅ Pam Seitz Test Passed!")

def test_reconciled_manual_logic():
    # Simulated Reconciled Manual Entry
    reconciled_data = {
        "PurchaseEx": {
            "any": [
                {
                    "value": {
                        "Name": "TxnType",
                        "Value": "54"
                    }
                }
            ]
        },
        "EntityRef": {
            "name": "Pam Seitz"
        },
        "Line": [
            {
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {
                        "name": "Legal & Professional Fees"
                    }
                }
            }
        ],
        "ClrStatus": "R" # Reconciled
    }

    print("\nTesting Reconciled Manual Entry...")
    is_matched, reason = FeedLogic.analyze(reconciled_data)
    print(f"Result: is_matched={is_matched}, reason='{reason}'")
    
    assert is_matched == True, f"Expected True, got {is_matched}"
    assert "Categorized Manual Entry" in reason, f"Unexpected reason: {reason}"
    print("✅ Reconciled Manual Test Passed!")

if __name__ == "__main__":
    try:
        test_pam_seitz_logic()
        test_reconciled_manual_logic()
        print("\n✨ All tests passed!")
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"💥 An error occurred: {e}")
        sys.exit(1)
