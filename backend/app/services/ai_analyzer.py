import google.generativeai as genai
import json
from app.core.config import settings
from app.core.prompts import TRANSACTION_ANALYSIS_PROMPT, RECEIPT_ANALYSIS_PROMPT, ANALYTICS_INSIGHTS_PROMPT
from rapidfuzz import process, fuzz

class AIAnalyzer:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.model = None

    def analyze_batch(self, transactions, context):
        """
        Analyzes a batch of transactions using Gemini Pro.
        context: {
            "category_list": [...],
            "history_str": "..."
        }
        """
        if not self.model:
            return {"error": "Gemini API Key missing"}

        tx_list_str = "\n".join([
            f"ID:{tx.id}|Desc:{tx.description}|Amt:{tx.amount} {tx.currency}|CurrentCategory:{tx.suggested_category_name or 'None'}" 
            for tx in transactions
        ])

        prompt = TRANSACTION_ANALYSIS_PROMPT.format(
            category_list=', '.join(context['category_list']),
            history_str=context['history_str'],
            tx_list_str=tx_list_str
        )
        
        try:
            # Force JSON mode
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            print(f"🧠 [AIAnalyzer] Raw AI Response: {raw_text[:500]}...") # Log start of response
            analyses = json.loads(raw_text)
            return analyses
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            # Fallback: return empty list to avoid crashing app
            return []

    def process_receipt(self, file_content: bytes):
        """
        Extracts data from receipt image using Gemini Vision.
        """
        if not self.model:
            raise ValueError("Gemini API Key missing")

        prompt = RECEIPT_ANALYSIS_PROMPT
        
        vision_result = self.model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": file_content}
        ])
        
        try:
            raw_text = vision_result.text.replace('```json', '').replace('```', '').strip()
            extracted = json.loads(raw_text)
            return extracted
        except Exception as e:
            print(f"❌ AI Receipt Error: {str(e)}")
            raise ValueError("Could not parse receipt data from AI")

    def generate_insights(self, events):
        """
        Analyzes user event logs to provide strategic insights.
        """
        if not self.model:
            return {"error": "Gemini API Key missing"}

        events_str = "\\n".join([
            f"[{e.timestamp}] User:{e.user_id[:8]}.. Action:{e.event_name} Props:{e.properties}" 
            for e in events
        ])

        prompt = ANALYTICS_INSIGHTS_PROMPT.format(events_str=events_str)
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(raw_text)
        except Exception as e:
            print(f"❌ AI Insights Error: {str(e)}")
            return {"error": "Failed to generate insights"}
