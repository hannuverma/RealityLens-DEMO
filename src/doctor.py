from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("MODELS ACCESSIBLE TO YOUR KEY:")
for m in client.models.list():
    # This will print something like 'gemini-1.5-flash' or 'gemini-1.5-flash-002'
    print(f" - {m.name}")