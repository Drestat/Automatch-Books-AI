import google.generativeai as genai
from sqlalchemy.orm import Session
from app.models.qbo import Transaction, Category, Customer
from app.core.config import settings
import json

class AIService:
    def __init__(self, db: Session):
        self.db = db
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def get_match_suggestions(self, realm_id: str):
        if not self.model:
            return []

        # Get unmatched transactions for this user
        transactions = self.db.query(Transaction).filter(
            Transaction.realm_id == realm_id,
            Transaction.status == 'unmatched'
        ).limit(10).all()

        if not transactions:
            return []

        # Get categories for context
        categories = self.db.query(Category).filter(Category.realm_id == realm_id).all()
        cat_names = [c.name for c in categories]

        suggestions = []
        for tx in transactions:
            prompt = f"""
            Analyze this bank transaction and suggest the best QuickBooks category.
            
            Transaction: {tx.description}
            Amount: {tx.amount} {tx.currency}
            
            Available Categories: {', '.join(cat_names)}
            
            Return ONLY a JSON object:
            {{
                "suggested_category_name": "string",
                "reasoning": "string (brief explanation)",
                "confidence": number (0-1)
            }}
            """
            try:
                response = self.model.generate_content(prompt)
                # Clean and parse JSON
                clean_json = response.text.replace('```json', '').replace('```', '').strip()
                result = json.loads(clean_json)
                
                tx.suggested_category_name = result.get("suggested_category_name")
                # Look up category id
                cat = next((c for c in categories if c.name == tx.suggested_category_name), None)
                if cat:
                    tx.suggested_category_id = cat.id
                
                tx.reasoning = result.get("reasoning")
                tx.confidence = result.get("confidence")
                tx.status = 'pending_approval'
                self.db.add(tx)
                suggestions.append(tx)
            except Exception as e:
                print(f"❌ AI Error for TX {tx.id}: {str(e)}")
        
        self.db.commit()
        return suggestions
