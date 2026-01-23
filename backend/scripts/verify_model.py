import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend root to sys.path for app imports
backend_root = Path(__file__).parent.parent
sys.path.append(str(backend_root))

# Load .env from root
load_dotenv(backend_root.parent / ".env")

import google.generativeai as genai
from app.core.config import settings

def verify():
    print(f"🚀 Verifying Gemini Model: {settings.GEMINI_MODEL}")
    
    if not settings.GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY is not set.")
        return

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        print("📡 Sending test prompt...")
        response = model.generate_content("Hello. Are you functional?")
        
        print(f"✅ Response received: {response.text[:50]}...")
        print(f"🎊 Gemini {settings.GEMINI_MODEL} is active and responding!")
        
    except Exception as e:
        print(f"❌ Verification Failed: {str(e)}")

if __name__ == "__main__":
    verify()
