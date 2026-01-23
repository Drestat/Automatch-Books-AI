# Technical Research Summary: Automatch Books AI Engine

## 1. QuickBooks Online API Detail
- **Discovery**: The QBO API V3 is the current stable version.
- **Library Recommendation (Python)**:
    - `intuit-oauth`: Essential for handling the OAuth 2.0 handshake and token management. It handles the nuances of Intuit's specific OAuth implementation.
    - `requests`: Given the complexity of some QBO objects, direct REST calls using `requests` are often more flexible than higher-level wrappers when dealing with specific edge cases in transaction data.
- **Library Recommendation (Node.js)**:
    - `node-quickbooks`: The most mature client for Node.js.
    - `apideck`: A strong alternative for type-safe, auto-generated SDKs.

## 2. Multi-Tenant Mirroring Strategy
- **Architectural Pattern**: "Local Copy / Remote Sync".
- **Database Schema**:
    - Every table MUST have a `realm_id` (QBO's tenant identifier).
    - Use JSONB columns for `raw_json` data to ensure no data is lost during the sync process and to allow for future AI re-processing without re-fetching from QBO.
- **Isolation**: Row-Level Security (RLS) in PostgreSQL is highly recommended to prevent cross-tenant data leakage at the database level.

## 3. Serverless Optimization (Modal)
- **Pattern**:
    - **FastAPI Function**: For interactive UI requests (lightweight).
    - **Modal Functions**: For heavy lifting (Syncing thousands of TXs, running Gemini analysis).
- **Concurrency**: Modal handles autoscaling naturally, making it easy to process multiple tenants in parallel without managing server clusters.

## 4. AI Logic (Gemini 1.5 Pro)
- **Token Efficiency**: Instead of sending all transactions one by one, batching related transactions (e.g., all purchases for a specific vendor) can improve categorization accuracy and reduce latency.
- **Contextual Anchors**: Providing the AI with a "Vendor Mapping" history from the mirror database significantly increases confidence scores.
