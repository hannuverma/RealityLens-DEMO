import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
keys = os.getenv("GEMINI_API_KEY", "").split(",")
keys = [k.strip() for k in keys if k.strip()]

for key in keys:
    try:
        client = genai.Client(api_key=key)
        r = client.models.generate_content(model="gemini-2.5-flash-lite", contents="hi")
        print(f"✅ Valid: {key[:8]}...")
    except Exception as e:
        print(f"❌ Invalid: {key[:8]}... → {str(e)[:80]}")