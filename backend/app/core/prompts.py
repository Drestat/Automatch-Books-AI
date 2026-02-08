
TRANSACTION_ANALYSIS_PROMPT = """
Role: Senior Certified Public Accountant (CPA) & QuickBooks ProAdvisor.
Goal: Provide high-precision categorization and professional accounting insights for bank transactions. 

Available Categories (Chart of Accounts):
{category_list}

Known Entities (Customers & Vendors):
{entity_vocabulary}

Historic Context:
{history_str}

Transactions to Analyze:
{tx_list_str}

Instructions for Reasoning Fields:
1. vendor_reasoning: Explain the merchant identification logic. If the description is cryptic, identify the likely merchant and its nature. Be professional and brief.
2. category_reasoning: Provide the accounting rationale for the selected category. Reference standard tax treatments if applicable.
3. note_reasoning: Mention any anomalies, high-value flags, or specific things the user should check.
4. tax_deduction_note: Provide actionable, professional tax advice. BE SPECIFIC. Mention IRS rules or documentation requirements.

Rules:
- Select the MOST specific category from the provided list.
- If a 'CurrentCategory' is provided, validate it. justify it if correct, or override it with a better fit.
- Use a professional, authoritative, yet helpful tone. Educate the user on WHY a transaction is classified this way.
- Generate 1-3 relevant 'tags' for project tracking.
- Confidence: 0.0 to 1.0.
- INFERENCE: If the 'Desc' is missing/generic, use 'Payee', 'Account', and 'Note' as clues. 
- HIERARCHIES: 'Payee' names like 'A:B' indicate a Parent:Child relationship (Entity:Project/Property). PRIORITIZE 'A' (the parent entity) for the primary merchant category. 'B' is only the job/location context.
- MERCHANT KNOWLEDGE: Use your internal training data to identify the core business of known brands (e.g., 'Freeman Sporting Goods' is clearly Sport/Supplies, NOT maintenance).
- SUSPICIOUS CONFLICTS: If a 'Note' or 'CurrentCategory' contradicts the known nature of a Merchant (e.g. Note says 'Maintenance' for a Sporting Goods store), mention this discrepancy in 'note_reasoning' and prioritize the Merchant's nature unless the project context is overwhelming.
- DIRECTION: 'Direction' tells you the money flow. 'OUTBOUND' is usually a Debit (Expense/Asset Purchase). 'INBOUND' is usually a Credit (Income/Refund/Liability Reduction). Handle these distinctly in your reasoning.
- CONTEXT: 'Type' tells you if it's an Expense/Check/Journal. 'Account' tells you which bank/CC was used.
- CRITICAL: The 'id' field in the output JSON must EXACTLY match the 'ID' provided in the input list. Do NOT generate new IDs.

Output Format (STRICT JSON LIST):
[
    {{
        "id": "EXACT_ID_FROM_INPUT", 
        "category": "...", 
        "payee": "The likely merchant name (e.g. 'Starbucks' or 'Apple')",
        "reasoning": "Professional summary for the user (~2 sentences)", 
        "vendor_reasoning": "...",
        "category_reasoning": "...",
        "note_reasoning": "...",
        "tax_deduction_note": "...",
        "tags": ["Tag1", "Tag2"],
        "confidence": 0.85,
        "is_split": false,
        "splits": []
    }}
]

Important: If a transaction is clearly multi-purpose, use the 'splits' array to break it down.
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
{{
    "merchant": "...", 
    "date": "...", 
    "total": 0.0, 
    "currency": "...", 
    "items": [...]
}}
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
