
TRANSACTION_ANALYSIS_PROMPT = """
Role: Senior Accountant AI for QuickBooks.
Goal: Categorize bank transactions using the standard Chart of Accounts because the user demands precision.

Available Categories:
{category_list}

Historic Patterns (For Context):
{history_str}

Transactions to Process:
{tx_list_str}

Rules:
1. Select the MOST specific category from the list above.
2. Provide THOROUGH, structured reasoning for your decision. 
   - vendor_reasoning: Explain how you identified the merchant (e.g., "SBUX" -> Starbucks).
   - category_reasoning: Why is this category correct? (e.g., "Coffee shop visit under $15 is typically Meals").
   - note_reasoning: Any additional context or flags (e.g., "High value for this vendor, flagged for review").
3. confidence: 0.0 to 1.0 based on how sure you are.

Output MUST be a valid JSON list of objects:
[
    {{
        "id": "...", 
        "suggested_category": "...", 
        "reasoning": "Legacy field - summarize here", 
        "vendor_reasoning": "...",
        "category_reasoning": "...",
        "note_reasoning": "...",
        "confidence": 0.0,
        "is_split": boolean,
        "splits": [
            {{"category": "...", "amount": 0.0, "description": "..."}}
        ]
    }}
]

Rule: If a transaction likely covers multiple categories (e.g., a "Target" run with both "Groceries" and "Home Supplies"), use the 'splits' array and set 'is_split' to true.
If splits are provided, the sum of split amounts MUST equal the transaction total.
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

ANALYTICS_INSIGHTS_PROMPT = """
Role: Product Analytics Expert.
Goal: Analyze user behavior logs to provide strategic insights for the app owner.

User Events Log:
{events_str}

Task:
1. Identify 3 key patterns (e.g., "Users drop off after sync", "Demo mode is highly engaging").
2. Provide 3 actionable suggestions to improve the app.
3. Highlight any anomalies.

Output JSON ONLY:
{{
    "patterns": ["...", "...", "..."],
    "suggestions": ["...", "...", "..."],
    "anomalies": ["..."]
}}
"""
