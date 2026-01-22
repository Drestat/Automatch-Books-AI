import os
import json
import sqlite3
from dotenv import load_dotenv
from tools.db_manager import DBManager

# Placeholder for actual Gemini interaction
# In a real scenario, we'd use the google-generativeai package
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class Navigation:
    def __init__(self):
        self.db = DBManager()
        if API_KEY:
            genai.configure(api_key=API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def get_context(self):
        """Fetches categories and customers to provide context to the AI"""
        with self.db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            categories = conn.execute("SELECT name FROM categories").fetchall()
            customers = conn.execute("SELECT display_name FROM customers").fetchall()
            return {
                "categories": [c['name'] for c in categories],
                "customers": [c['display_name'] for c in customers]
            }

    def analyze_transaction(self, tx):
        """Uses Gemini to analyze a single transaction"""
        if not self.model:
            return {"suggested_category": "Manual Review Needed", "reasoning": "Gemini API Key missing", "confidence": 0}

        context = self.get_context()
        prompt = f"""
        Analyze this bank transaction and suggest the best QuickBooks category.
        
        Transaction: {tx['description']}
        Amount: {tx['amount']} {tx['currency']}
        
        Available Categories: {', '.join(context['categories'][:50])}
        
        Return JSON format:
        {{
            "suggested_category": "string",
            "reasoning": "brief explanation",
            "confidence": 0.0 to 1.0
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Simple JSON parsing from response text
            # In production, use more robust parsing/structured output
            result = json.loads(response.text.strip('`json\n'))
            return result
        except Exception as e:
            print(f"❌ AI Error: {str(e)}")
            return {"suggested_category": "Error", "reasoning": str(e), "confidence": 0}

    def process_unmatched(self):
        print("🧠 Starting AI Reasoning for unmatched transactions...")
        unmatched = self.db.get_unmatched_transactions()
        
        for tx in unmatched[:5]: # Limit for testing
            print(f"🔍 Analyzing: {tx['description']}")
            analysis = self.analyze_transaction(tx)
            
            # Update the mirror with the suggestion
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE transactions 
                    SET suggested_category_name = ?, reasoning = ?, confidence = ?, status = 'pending_approval'
                    WHERE id = ?
                """, (analysis['suggested_category'], analysis['reasoning'], analysis['confidence'], tx['id']))
        
        print(f"✅ AI reasoning complete for {len(unmatched[:5])} transactions.")

if __name__ == "__main__":
    nav = Navigation()
    # Before processing, we need some categories in the DB for context
    # This would normally happen in the sync engine
    nav.process_unmatched()
