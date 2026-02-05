import modal
from dotenv import dotenv_values

app = modal.App("query-qbo-pam")
env_vars = dotenv_values(".env")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "requests", "httpx", "pydantic-settings", "intuit-oauth")
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

@app.local_entrypoint()
def main():
    query_pam.remote()

@app.function(image=image)
def query_pam():
    from app.services.qbo_client import QBOClient
    from app.models.qbo import QBOConnection
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get first connection (assuming only 1 user/realm for now)
        connection = db.query(QBOConnection).first()
        if not connection:
            print("No QBO Connection found.")
            return

        client = QBOClient(db, connection)
        
        print(f"Querying QBO for Pam Seitz on Realm {connection.realm_id}...")
        
        # Query Vendor to get ID
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_queries():
            # 1. Find Vendor
            vendor_query = "SELECT * FROM Vendor WHERE DisplayName LIKE '%Pam%'"
            v_res = await client.query(vendor_query)
            vendors = v_res.get("QueryResponse", {}).get("Vendor", [])
            print(f"Found {len(vendors)} vendors matching 'Pam'.")
            
            for v in vendors:
                print(f"Vendor: {v['DisplayName']} (Id: {v['Id']})")
                
                # 2. Find BillPayments for this Vendor
                try:
                    bp_query = f"SELECT * FROM BillPayment WHERE VendorRef = '{v['Id']}'"
                    bp_res = await client.query(bp_query)
                    bps = bp_res.get("QueryResponse", {}).get("BillPayment", [])
                    print(f"  Found {len(bps)} BillPayments.")
                    for bp in bps:
                        print(f"  - ID: {bp['Id']}, TotalAmt: {bp['TotalAmt']}, Date: {bp['TxnDate']}")
                except Exception as e:
                    print(f"  ❌ Error querying BillPayment: {e}")

                # 3. Find Purchases for this Vendor
                try:
                    # EntityRef might not be filterable? Try filtering by Payee? No, Payee is mapped.
                    # QBO docs say: "AccountRef, EntityRef, TxnDate, TotalAmt, ..."
                    # Maybe it requires checking if EntityRef is a supported filter.
                    # Let's try listing all purchases and filtering manually if query fails?
                    # Or try selecting just ID first?
                    
                    p_query = f"SELECT * FROM Purchase WHERE EntityRef = '{v['Id']}'"
                    p_res = await client.query(p_query)
                    ps = p_res.get("QueryResponse", {}).get("Purchase", [])
                    print(f"  Found {len(ps)} Purchases.")
                    for p in ps:
                        print(f"  - ID: {p['Id']}, TotalAmt: {p['TotalAmt']}, Date: {p['TxnDate']}")
                except Exception as e:
                     print(f"  ❌ Error querying Purchase: {e}")
                     # Fallback: List recent purchases and filter manually
                     try:
                         print("    Attempting fallback: List 100 purchases and filter locally...")
                         fb_query = "SELECT * FROM Purchase MAXRESULTS 100"
                         fb_res = await client.query(fb_query)
                         all_ps = fb_res.get("QueryResponse", {}).get("Purchase", [])
                         matched_ps = [p for p in all_ps if p.get("EntityRef", {}).get("value") == v["Id"]]
                         print(f"    Found {len(matched_ps)} purchases containing vendor locally.")
                         for p in matched_ps:
                             print(f"    - ID: {p['Id']}, TotalAmt: {p['TotalAmt']}, Date: {p['TxnDate']}")
                     except Exception as ex:
                         print(f"    ❌ Fallback also failed: {ex}")

                # 4. Find JournalEntry (manual filter)
                try:
                     je_query = "SELECT * FROM JournalEntry MAXRESULTS 500"
                     je_res = await client.query(je_query)
                     jes = je_res.get("QueryResponse", {}).get("JournalEntry", [])
                     matched_jes = []
                     for je in jes:
                         for line in je.get("Line", []):
                             # JournalEntryLineDetail -> Entity -> EntityRef
                             details = line.get("JournalEntryLineDetail", {})
                             entity = details.get("Entity", {})
                             if entity.get("EntityRef", {}).get("value") == v["Id"]:
                                 matched_jes.append(je)
                                 break
                     print(f"  Found {len(matched_jes)} JournalEntries.")
                     for je in matched_jes:
                         print(f"  - ID: {je['Id']}, TotalAmt: {je['TotalAmt']}, Date: {je['TxnDate']}")
                except Exception as e:
                    print(f"  ❌ Error querying JournalEntry: {e}")
                
                # 5. Find CreditCardCredit
                try:
                    # Try filtering locally to be safe
                    cc_query = "SELECT * FROM CreditCardCredit MAXRESULTS 100"
                    cc_res = await client.query(cc_query)
                    ccs = cc_res.get("QueryResponse", {}).get("CreditCardCredit", [])
                    matched_ccs = [c for c in ccs if c.get("EntityRef", {}).get("value") == v["Id"]]
                    print(f"  Found {len(matched_ccs)} CreditCardCredits.")
                    for c in matched_ccs:
                         print(f"  - ID: {c['Id']}, TotalAmt: {c['TotalAmt']}, Date: {c['TxnDate']}")
                except Exception as e:
                    print(f"  ❌ Error querying CreditCardCredit: {e}")

            # 6. Check Customers
            cust_query = "SELECT * FROM Customer WHERE DisplayName LIKE '%Pam%'"
            c_res = await client.query(cust_query)
            customers = c_res.get("QueryResponse", {}).get("Customer", [])
            print(f"Found {len(customers)} customers matching 'Pam'.")
            
            for c in customers:
                print(f"Customer: {c['DisplayName']} (Id: {c['Id']})")
                
                # Check Payments (from customer)
                pay_query = f"SELECT * FROM Payment WHERE CustomerRef = '{c['Id']}'"
                pay_res = await client.query(pay_query)
                pays = pay_res.get("QueryResponse", {}).get("Payment", [])
                print(f"  Found {len(pays)} Payments.")
                for p in pays:
                    print(f"  - ID: {p['Id']}, TotalAmt: {p['TotalAmt']}, Date: {p['TxnDate']}")
                
                # Check Deposits (could contain customer)
                # Deposits are complex, contains lines. Paging filtering locally is best if volume is low.
                # Or query linked lines.
                pass
        
        loop.run_until_complete(run_queries())
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
