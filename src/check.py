from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
# Make sure your .env has GEMINI_API_KEY=AIza...
MODELS = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
    ]

api_keys = os.getenv("GEMINI_API_KEY", "").split(",")
api_keys = [k.strip() for k in api_keys if k.strip()]

def test_connection():
    print("🚀 Attempting connection with Stable Flash 1.5...")
    api_key = os.getenv("GEMINI_API_KEY_1")
    for model in MODELS:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model, contents="say \"hello\" if you are an ai are reading this")

            if response.text and "hello" in response.text.lower():
                print(f"✅ Connected successfully with key: {api_key[:4]}...{api_key[-4:]} using model {model}")
            else:
                print(f"⚠️ Connected with key: {api_key[:4]}...{api_key[-4:]} but got unexpected response: {response.text}")

        except Exception as e:
            print(f"❌ Connection failed with key: {api_key[:4]}...{api_key[-4:]} - {e}")
    return

if __name__ == "__main__":
    test_connection()