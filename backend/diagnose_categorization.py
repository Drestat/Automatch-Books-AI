"""
Diagnostic script to check which transactions have TxnType=54 and why they're categorized
Run with: modal run modal_app.py::diagnose_categorization --realm-id YOUR_REALM_ID
"""
import modal
from app.services.qbo_client import QBOClient
from app.db.session import get_db
from app.models.qbo import QBOConnection

app = modal.App.lookup("qbo-sync-engine", create_if_missing=False)

@app.function()
def diagnose_categorization(realm_id: str):
    """Diagnose which transactions are being marked as categorized and why"""
    db = next(get_db())
    
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print(f"❌ No connection found for realm_id: {realm_id}")
            return
        
        client = QBOClient(db, connection)
        
        # Query all Purchase transactions
        query = "SELECT * FROM Purchase MAXRESULTS 1000"
        result = client.query(query)
        
        purchases = result.get("QueryResponse", {}).get("Purchase", [])
        print(f"\n📊 Found {len(purchases)} total Purchase transactions\n")
        
        categorized = []
        for_review = []
        
        for p in purchases:
            tx_id = p.get("Id")
            description = p.get("EntityRef", {}).get("name", "No description")
            total = p.get("TotalAmt", 0)
            
            # Check for LinkedTxn
            has_linked_txn = len(p.get("LinkedTxn", [])) > 0
            
            # Check for TxnType=54
            is_manually_categorized = False
            purchase_ex = p.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
                        if txn_type == "54":
                            is_manually_categorized = True
                            break
            
            # Get category from Lines
            category = "No category"
            if "Line" in p:
                for line in p["Line"]:
                    if "AccountBasedExpenseLineDetail" in line:
                        detail = line["AccountBasedExpenseLineDetail"]
                        if "AccountRef" in detail:
                            category = detail["AccountRef"].get("name", "No category")
                            break
            
            tx_info = {
                "id": tx_id,
                "description": description,
                "amount": total,
                "category": category,
                "has_linked_txn": has_linked_txn,
                "txn_type_54": is_manually_categorized
            }
            
            if has_linked_txn or is_manually_categorized:
                categorized.append(tx_info)
            else:
                for_review.append(tx_info)
        
        print(f"✅ CATEGORIZED ({len(categorized)} transactions):")
        print("=" * 80)
        for tx in categorized:
            reason = []
            if tx["has_linked_txn"]:
                reason.append("LinkedTxn")
            if tx["txn_type_54"]:
                reason.append("TxnType=54")
            
            print(f"ID: {tx['id']}")
            print(f"  Description: {tx['description']}")
            print(f"  Amount: ${tx['amount']}")
            print(f"  Category: {tx['category']}")
            print(f"  Reason: {' + '.join(reason)}")
            print()
        
        print(f"\n📋 FOR REVIEW ({len(for_review)} transactions):")
        print("=" * 80)
        for tx in for_review[:5]:  # Show first 5
            print(f"ID: {tx['id']}")
            print(f"  Description: {tx['description']}")
            print(f"  Amount: ${tx['amount']}")
            print(f"  Category: {tx['category']}")
            print()
        
        if len(for_review) > 5:
            print(f"... and {len(for_review) - 5} more\n")
        
        return {
            "categorized_count": len(categorized),
            "for_review_count": len(for_review),
            "categorized": categorized,
            "for_review": for_review
        }
        
    finally:
        db.close()
