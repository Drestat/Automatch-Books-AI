# AutoMatch Books AI 🔮

**The Magical Mirror for QuickBooks Online.**

AutoMatch Books AI is a next-generation SaaS platform that automates financial reconciliation using **Google Gemini 1.5 Pro/Flash** (Hybrid Intelligence). Unlike "black box" automation tools, we provide **auditable intelligence**—the AI explains its logic for every transaction, and the user is the "final boss" who validates and clicks "Agree." We are the human-in-the-loop trust bridge missing in fintech.

---

## 🚀 Key Features

*   **Zero-Lag Sync**: Kinetic UI that feels instant, powered by optimistic updates and background syncing.
*   **Hybrid Intelligence**:
    *   **Auditable AI**: Every categorization comes with a transparent reasoning narrative.
    *   **Human-in-the-Loop**: Automation that saves time without sacrificing control.
    *   **Determinism**: Automatic matching for known vendors.
*   **Superior Analytics & Tags**: Multi-dimensional filtering that goes beyond QuickBooks' native capabilities.
*   **Transaction Splitting**: AI automatically detects and splits multi-category receipts (e.g., "Target" -> Groceries & Home Supplies).
*   **The Velvet Rope**: Glassmorphic SaaS Paywall strategies with Stripe integration.
*   **Receipt Mirroring**: Upload receipts to transactions with auto-matching.
*   **Bank-Grade Security**: AES-256 encryption, Clerk Authentication, and RLS (Row Level Security).

---

## 🏗️ Architecture

### Tech Stack
*   **Frontend**: Next.js 14, Tailwind CSS, Framer Motion (Glassmorphism UI).
*   **Backend**: Python FastAPI (Async), SQLAlchemy.
*   **Database**: PostgreSQL (Multi-tenant with RLS).
*   **AI**: Google Gemini 1.5 Pro / 3 Flash.
*   **Auth**: Clerk (SaaS Identity Management).
*   **Payments**: Stripe (Checkout & Webhooks).

### System Flow
1.  **User** logs in via Clerk.
2.  **App** mirrors QBO data to local Postgres.
3.  **Gemini AI** analyzes unmatched transactions in batches.
4.  **User** approves/edits suggestions in the "Magical Mirror" Dashboard.
5.  **Sync Engine** pushes changes back to QuickBooks Online.

---

## 🛠️ Setup & Installation

### Prerequisites
*   Node.js 18+ & Python 3.9+
*   PostgreSQL Database
*   QuickBooks Online Developer Account
*   Stripe Account
*   Clerk Account
*   Google Gemini API Key

### 1. Environment Variables
Create a `.env` file in the root:
```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost/automatch
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-3-flash-preview
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# Frontend
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 2. Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:3001
```

### 4. Webhooks
Run the Stripe listener for local dev:
```bash
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

---

## 🛡️ License
Private Proprietary Software. © 2026 AutoMatch Books AI Engine.
