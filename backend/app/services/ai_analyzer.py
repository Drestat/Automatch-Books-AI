import google.generativeai as genai
import json
from app.core.config import settings
from app.core.prompts import TRANSACTION_ANALYSIS_PROMPT, RECEIPT_ANALYSIS_PROMPT
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
            f"ID:{tx.id}|Desc:{tx.description}|Amt:{tx.amount} {tx.currency}" 
            for tx in transactions
        ])

        prompt = TRANSACTION_ANALYSIS_PROMPT.format(
            category_list=', '.join(context['category_list']),
            history_str=context['history_str'],
            tx_list_str=tx_list_str
        )
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            analyses = json.loads(raw_text)
            return analyses
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            raise e

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
