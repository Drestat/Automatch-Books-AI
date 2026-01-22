# SOP: Bank Transaction Matching Logic

## Overview
This SOP defines the deterministic process for matching raw bank transactions to QuickBooks categories and records using a hybrid SQL + AI approach.

## 1. Data Retrieval (The Mirror)
All reasoning is performed against the **Local SQLite Mirror** (`.tmp/mirror.db`).
- Transactions are pulled where `status = 'unmatched'`.
- Reference data (Customers, Categories) is synced from QBO to the mirror before matching.

## 2. AI Prompting (The Reasoning)
Google Gemini is used to analyze each transaction.
Input to Gemini:
- Transaction Description, Amount, Date.
- List of available QuickBooks Categories.
- List of active Customers.

## 3. Categorization Rules
- **Rule 1: Exact Match.** If the description matches a known Vendor/Merchant name exactly, assign the previous category used for that vendor.
- **Rule 2: AI Guess.** If no exact match, Gemini suggests the best category with a "Reasoning Narrative".
- **Rule 3: Confidence Threshold.**
    - Confidence > 0.8: Suggest as "Highly Likely".
    - Confidence < 0.5: Mark for manual review with a warning.

## 4. Human-In-The-Loop (HITL)
- NO transaction is written back to QuickBooks until the user clicks **Accept** in the UI.
- Acceptance triggers a SQL update to the Mirror (`status = 'approved'`) and then a POST to the QBO API.
