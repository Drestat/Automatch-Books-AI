
from app.db.session import SessionLocal
from app.models.qbo import Transaction
from app.core.feed_logic import FeedLogic
import sys

db = SessionLocal()

# Test Candidates
candidates = [
    {"term": "Lara's Lamination", "expected": True, "desc": "Reconciled Manual (Lara)"},
    {"term": "Hicks Hardware", "expected": False, "desc": "QBO Suggestion (Hicks)"},
    {"term": "A Rental", "expected": False, "desc": "Bill Payment (A Rental)"},
    {"term": "Pam Seitz", "expected": False, "desc": "Unreconciled Manual (Pam)"},
    {"term": "Books by Bessie", "expected": True, "desc": "Categorized Deposit (Bessie)"}
]

print(f"{'Test Case':<30} | {'Status':<6} | {'Logic Match':<11} | {'Reason'}")
print("-" * 120)

all_passed = True

for cand in candidates:
    txs = db.query(Transaction).filter(Transaction.description.ilike(f"%{cand['term']}%")).all()
    # Pick the most relevant one (sometimes duplicates exist, pick matching ID if known, or just check all)
    # Check specifically for the Type we care about
    found = False
    for tx in txs:
        if not tx.raw_json:
            continue
            
        # Refine Selection
        if cand['term'] == "Books by Bessie":
             # Only check the Deposit one (ID 146 or amount 55.00?)
             if "DepositLineDetail" not in str(tx.raw_json):
                 continue 
        
        # Run Logic
        is_matched, reason = FeedLogic.analyze(tx.raw_json)
        
        status = "PASS" if is_matched == cand['expected'] else "FAIL"
        if status == "FAIL":
            all_passed = False
            
        print(f"{cand['desc']:<30} | {status:<6} | {str(is_matched):<11} | {reason}")
        found = True
        break # Just check one representative
    
    if not found:
        print(f"{cand['desc']:<30} | SKIP   | N/A         | Transaction not found in DB")

db.close()

if all_passed:
    print("\n✅ ALL SCENARIOS PASSED")
else:
    print("\n❌ SOME SCENARIOS FAILED")
