# Gemini: Project Map & Source of Truth

## Project Overview
- **Name**: Automatch Books AI
- **Status**: Discovery / Phase 1: Blueprint
- **Owner**: System Pilot (Antigravity)

## 0. Protocol 0: Initialization
- [x] `gemini.md` initialized.
- [x] Directory structure created (`architecture/`, `tools/`, `.tmp/`).
- [ ] Discovery Questions answered.
- [ ] Data Schema defined.
- [ ] Blueprint approved.

## 1. Discovery (B.L.A.S.T. Phase 1)
- **North Star**: A multi-user SaaS application (Web + Mobile App) where business owners login, connect their QuickBooks, and approve daily AI-categorized bank transactions.
- **Integrations**:
    - **QuickBooks Online (QBO) OAuth 2.0**: Multi-tenant authorization.
    - **PostgreSQL**: Multi-tenant "Mirror" database (migrated from SQLite).
    - **Next.js & Tailwind CSS**: For a premium, responsive, glassmorphic UI.
    - **Google Gemini API**: Cognitive engine for cross-user transaction matching.
    - **Capacitor / Expo**: For packaging the web app as a native mobile app.
    - **Clerk / Supabase Auth**: Secure multi-user login.
- **Source of Truth**: Multi-tenant PostgreSQL Mirror.
- **Delivery Payload**:
    - **SaaS Backend**: Manages sync/auth/reasoning for multiple users.
    - **Mobile/Web Dashboards**: Responsive UI with "Accept" actions.
    - **Elegant Analytics Engine**: Interactive data visualizations (Recharts) for project spend and vendor analysis.
    - **Scalable Sync Engine**: Background processing for daily categorizations.
- **Behavioral Rules**:
    - AI must provide "why" for every categorization choice.
    - Human-in-the-loop: No write-back without user acceptance.
    - Analytics must be visually "Awe-Striking" (Glow effects, smooth transitions).
    - Provide deep-dives into "Subcontractors" and "Project Tags".
    - Direct SQL interaction against the Multi-tenant PostgreSQL Mirror.

## 2. Data Schema (JSON)

### Input Shape (Raw Bank Transaction for AI Reasoning)
```json
{
  "transaction_id": "string (QBO Id)",
  "date": "string (ISO-8601)",
  "description": "string",
  "amount": "number",
  "currency": "string",
  "source_account": {
    "id": "string",
    "name": "string"
  },
  "metadata": {
    "merchant_name": "string",
    "category_guess": "string"
  }
}
```

### AI Analysis Shape (The "Why")
```json
{
  "transaction_id": "string",
  "suggested_category": {
    "id": "string",
    "name": "string"
  },
  "matching_record": {
    "type": "invoice | bill | payment",
    "id": "string",
    "confidence": "number (0-1)"
  },
  "reasoning_narrative": "string (The 'why')",
  "confidence_score": "number"
}
```

### Output Shape (Write-Back Payload)
```json
{
  "action": "match | categorize | skip",
  "target_record_id": "string",
  "status": "approved",
  "user_id": "string",
  "timestamp": "string (ISO-8601)"
}
```

## 3. Maintenance Log
| Date | Action | Result |
| :--- | :--- | :--- |
| 2026-01-22 | Initialized Protocol 0 | Project map ready. |
