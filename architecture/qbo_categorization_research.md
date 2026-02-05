# Research: QBO Transaction Categorization Movement

## The Problem
QBO Bank Feed transactions (the "Banking" tab) are in a "limbo" state until they are "Accepted" or "Matched". The standard QuickBooks Online V3 API does not provide a direct endpoint to "Accept" or "Match" bank transactions.

## Technical Findings

### 1. The Banking Feed visibility
- Transactions in "For Review" are bank feed entries that QBO exposes in the API as `Purchase`, `Deposit`, or `CreditCardCredit` entities with specific metadata.
- **Matched** transactions in the feed have a `LinkedTxn` pointing to a register entry.
- **Unmatched** transactions are entries QBO "shadow-created" in the register but marked as unconfirmed.

### 2. The Movement Trigger (`ClrStatus`)
Research indicates that the "hidden switch" to move a transaction from "For Review" to "Categorized" in the QBO UI via the API is the **`ClrStatus`** (Clearance Status) field.

- **Entity**: `Purchase`, `Deposit`, `JournalEntry`
- **Field Path**: `Line.AccountBasedExpenseLineDetail.ClrStatus`
- **Value**: `Cleared` (signals the transaction is accepted/processed).
- **Result**: Setting `ClrStatus` to `Cleared` (and providing a specific Category/Payee) typically satisfies QBO's reconciliation logic, moving it out of "For Review".

### 3. Bill Matching Logic
For matching existing `Bills` to bank feed entries:
- **Action**: Create a `BillPayment` object.
- **Linking**: Use the `LinkedTxn` field inside the `BillPayment` to point to the `TxnId` of the `Bill`.
- **UI Effect**: QBO detects the payment on the bank account and "Greens" the match in the Banking tab, effectively categorizing it.

### 4. Persistent Tracking (`#Accepted` Marker)
To ensure the app and QBO stay in parity (even if a user manually changes things in QBO), we use a persistent marker.
- **Location**: `PrivateNote` (Memo).
- **Marker**: `#Accepted`.
- **Rationale**: Since `LinkedTxn` for bank events is not accessible/storable via API, this marker survives sync cycles and acts as an immutable flag for our AI engine.

## Recommended Architecture for Implementation

### Sparse Update Payload (Purchase)
To "Accept" an expense:
```json
{
  "Id": "123",
  "SyncToken": "1",
  "sparse": true,
  "PrivateNote": "Approved by AI | #Accepted",
  "Line": [
    {
      "Id": "1",
      "DetailType": "AccountBasedExpenseLineDetail",
      "AccountBasedExpenseLineDetail": {
        "AccountRef": { "value": "TARGET_CAT_ID" },
        "ClrStatus": "Cleared"
      }
    }
  ]
}
```

### Bill Match Payload (BillPayment)
To match a Bill:
```json
{
  "TxnDate": "2026-02-04",
  "PayType": "Check",
  "CheckPayment": {
    "BankAccountRef": { "value": "BANK_ACC_ID" }
  },
  "Line": [
    {
      "Amount": 150.00,
      "LinkedTxn": [
        { "TxnId": "BILL_ID", "TxnType": "Bill" }
      ]
    }
  ]
}
```

## Summary for Builder
- Use `update_purchase` with `ClrStatus='Cleared'`.
- Append `#Accepted` to `PrivateNote`.
- Implement `create_bill_payment` for Bill-based transactions.
- Update `FeedLogic` to recognize these states as "Categorized".
