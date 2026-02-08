try:
    import google.generativeai as genai
except ImportError:
    genai = None

import json
from app.core.config import settings
from app.core.prompts import TRANSACTION_ANALYSIS_PROMPT, RECEIPT_ANALYSIS_PROMPT, ANALYTICS_INSIGHTS_PROMPT
from rapidfuzz import process, fuzz

class AIAnalyzer:
    def __init__(self):
        if genai and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            print("⚠️ [AIAnalyzer] Generative AI not available (Missing lib or Key)")
            self.model = None

    def analyze_batch(self, transactions, context):
        """
        Analyzes a batch of transactions using Gemini Pro.
        context: {
            "category_list": [...],
            "history_str": "...",
            "entity_vocabulary": [...]
        }
        """
        if not self.model:
            return {"error": "Gemini API Key missing"}

        def get_direction(t_type):
            if t_type in ["Purchase", "Check", "CreditCard", "BillPayment"]:
                return "OUTBOUND (Spending/Expense)"
            if t_type in ["Deposit", "Payment", "CreditCardCredit"]:
                return "INBOUND (Income/Refund/Credit)"
            return "NEUTRAL/TRANSFERRED"

        tx_list_str = "\n".join([
            f"ID:{tx.id}|Direction:{get_direction(tx.transaction_type)}|Type:{tx.transaction_type}|Desc:{tx.description}|Payee:{tx.payee}|Account:{tx.account_name}|Amt:{tx.amount} {tx.currency}|Note:{tx.note}|CurrentCategory:{tx.suggested_category_name or 'None'}" 
            for tx in transactions
        ])

        prompt = TRANSACTION_ANALYSIS_PROMPT.format(
            category_list=', '.join(context['category_list']),
            entity_vocabulary=', '.join(context.get('entity_vocabulary', [])[:100]), # Limit vocabulary for prompt length
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
            print(f"🧠 [AIAnalyzer] Raw AI Response Length: {len(raw_text)}")
            if len(raw_text) > 0:
                print(f"🧠 [AIAnalyzer] Raw AI Response (First 1000 chars): {raw_text[:1000]}")
            
            analyses = json.loads(raw_text)
            
            # Basic validation of expected fields
            if isinstance(analyses, list) and len(analyses) > 0:
                first = analyses[0]
                missing = [f for f in ["vendor_reasoning", "category_reasoning", "tax_deduction_note"] if f not in first]
                if missing:
                    print(f"⚠️ [AIAnalyzer] Missing reasoning fields in AI output: {missing}")
                else:
                    print(f"✅ [AIAnalyzer] All reasoning fields present in AI output.")
            
            return analyses
        except Exception as e:
            print(f"❌ Batch AI Error: {str(e)}")
            # Fallback: return empty list to avoid crashing app
            return []

    def process_receipt(self, file_content: bytes, mime_type: str = "image/jpeg"):
        """
        Extracts data from receipt image using Gemini Vision.
        """
        if not self.model:
            raise ValueError("Gemini API Key missing")

        prompt = RECEIPT_ANALYSIS_PROMPT
        
        vision_result = self.model.generate_content(
            [prompt, {"mime_type": mime_type, "data": file_content}],
            generation_config={"response_mime_type": "application/json"}
        )
        
        try:
            # Clean possible markdown artifacts even if response_mime_type is set (safety)
            raw_text = vision_result.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
                raw_text = raw_text.rsplit("\n", 1)[0] if "\n" in raw_text else raw_text
                raw_text = raw_text.replace("json", "", 1).strip()
            
            print(f"📊 [AIAnalyzer] Extracted Receipt: {raw_text[:500]}...")
            extracted = json.loads(raw_text)
            return extracted
        except Exception as e:
            print(f"❌ AI Receipt Error: {str(e)}")
            if 'vision_result' in locals() and hasattr(vision_result, 'text'):
                 print(f"❌ Raw text that failed: {vision_result.text}")
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
