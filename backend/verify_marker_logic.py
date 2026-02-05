from app.core.feed_logic import FeedLogic
import json

def test_accepted_marker():
    print("🧪 Testing #Accepted marker logic...")
    
    # 1. Transaction WITH #Accepted marker
    tx_with_marker = {
        "Id": "123",
        "SyncToken": "1",
        "PrivateNote": "Some note | #Accepted",
        "PurchaseEx": {
            "any": [{"value": {"Name": "TxnType", "Value": "54"}}]
        },
        "Line": []
    }
    
    is_matched, reason = FeedLogic.analyze(tx_with_marker)
    print(f"Transaction with marker: is_matched={is_matched}, reason='{reason}'")
    assert is_matched == True
    assert "Found #Accepted marker" in reason
    
    # 2. Transaction WITHOUT #Accepted marker (Manual entry, not reconciled)
    tx_without_marker = {
        "Id": "124",
        "SyncToken": "1",
        "PrivateNote": "Just a regular note",
        "PurchaseEx": {
            "any": [{"value": {"Name": "TxnType", "Value": "54"}}]
        },
        "Line": [
            {
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {"name": "Meals and Entertainment", "value": "13"}
                },
                "ClrStatus": "Create"
            }
        ]
    }
    
    # Need to mock more fields for proper analysis if we want full check, 
    # but for marker check, it should just pass.
    is_matched, reason = FeedLogic.analyze(tx_without_marker)
    print(f"Transaction without marker: is_matched={is_matched}, reason='{reason}'")
    # This should be False because it's a Type 54 and not reconciled
    assert is_matched == False
    
    print("\n✅ Verification successful!")

if __name__ == "__main__":
    test_accepted_marker()
