from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
# Make sure your .env has GEMINI_API_KEY=AIza...
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  

def test_connection():
    print("🚀 Attempting connection with Stable Flash 1.5...")
    try:
        # FIX: No leading space, no 'models/' prefix
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents="Say 'RealityLens is Online' if you can read this."
        )
        print(f"✅ AI Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_connection()