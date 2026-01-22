# Backend Plan: QuickBooks AI Matching Engine

This document outlines the architecture and implementation status of the "Engine" for the QuickBooks Bank Transactions application.

## 1. Architecture Overview
- **Core API**: FastAPI (Python) running in `backend/`.
- **Mirror Database**: PostgreSQL for multi-tenant data storage.
- **Serverless Infrastructure**: Modal for long-running sync and AI jobs.
- **AI Engine**: Google Gemini 1.5 Pro for transaction categorization.

## 2. Serverless Endpoints (Modal)
The following endpoints are implemented in `backend/modal_app.py`:

| Function | Type | Description |
| :--- | :--- | :--- |
| `sync_user_data` | Async/Remote | Pulls raw purchase data, categories, and customers from QBO. |
| `process_ai_categorization` | Async/Remote | Runs Gemini analysis on unmatched transactions. |
| `daily_maintenance` | Scheduled | Daily CRON job to refresh all tenant data. |

## 3. API Routes (FastAPI)
Implemented in `backend/app/api/v1/endpoints/`:

- **QBO Auth**:
  - `GET /authorize`: Starts OAuth 2.0 flow.
  - `GET /callback`: Handles QBO redirect and token storage.
- **Transactions**:
  - `GET /`: Lists transactions for a specific realm.
  - `POST /sync`: Triggers Modal sync job (background).
  - `POST /analyze`: Triggers Gemini categorization (background). Supports `tx_id` for immediate processing.

## 4. Optimization Engine
- **Batching**: AI analyzes up to 20 transactions per request for token efficiency.
- **Vendor History**: Pulls approved mappings to provide context to the AI (Higher accuracy).
- **Date Prioritization**: Newest transactions are always processed first.
- **Token Pruning**: Context is stripped to essential data to minimize costs.

## 5. Next Steps
- [x] Establish QBO OAuth 2.0 flow.
- [x] Build multi-tenant PostgreSQL mirror.
- [x] Implement Modal serverless functions.
- [x] Integrate Gemini with batching and history context.
- [ ] Add error handling for QBO API rate limits.
- [ ] Implement secure webhook listener for real-time QBO updates.
