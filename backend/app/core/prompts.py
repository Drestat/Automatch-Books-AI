
TRANSACTION_ANALYSIS_PROMPT = """
Role: Senior Accountant AI for QuickBooks.
Goal: Categorize bank transactions using the standard Chart of Accounts.

Available Categories:
{category_list}

Historic Patterns (For Context):
{history_str}

Transactions to Process:
{tx_list_str}

Rules:
1. Select the MOST specific category from the list above.
2. reasoning: Brief, high-signal explanation (e.g. "Typical recurring SaaS pattern" or "Utility bill match"). Max 12 words.
3. confidence: 0.0 to 1.0 based on how sure you are.

Output MUST be a valid JSON list of objects:
[
    {{
        "id": "...", 
        "suggested_category": "...", 
        "reasoning": "...", 
        "confidence": 0.0,
        "splits": [
            {{"category": "...", "amount": 0.0, "description": "..."}}
        ]
    }}
]

Rule: If a transaction likely covers multiple categories (e.g., a "Target" run with both "Groceries" and "Home Supplies"), use the 'splits' array and set 'is_split' to true.
If splits are provided, the sum of split amounts MUST equal the transaction total.
Output JSON object for each transaction MUST include:
{{
    "id": "...", 
    "suggested_category": "...", 
    "reasoning": "...", 
    "confidence": 0.0, 
    "is_split": boolean,
    "splits": [
        {{"category": "...", "amount": 0.0, "description": "..."}}
    ]
}}
"""

RECEIPT_ANALYSIS_PROMPT = """
Analyze this receipt image. 
Extract: 
1. Merchant Name
2. Date (YYYY-MM-DD)
3. Total Amount
4. Currency
5. Items (JSON list)

Return JSON ONLY:
{{"merchant": "...", "date": "...", "total": 0.0, "currency": "...", "items": [...]}}
"""
