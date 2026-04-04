import sys

from google import genai
from google.genai import types # Added for versioning
import os
import re
from PIL import Image
from dotenv import load_dotenv

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


load_dotenv(resource_path(".env"))

api_key = os.getenv("GEMINI_API_KEY")
    


client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version='v1')
)


def verify_content(image_path):
    if not api_key:
        return "RealityLens config error: GEMINI_API_KEY is missing."

    try:
        img = Image.open(image_path)
        
        # This is the exact string confirmed by your doctor.py output
        model_name = "gemini-2.5-flash" 

        prompt = """
        You are RealityLens, a professional fact-checker. 
        Analyze this image snippet. 
        1. Identify the central claim.
        2. Verdict: [Likely Real | Suspicious | Likely Fake]
        3. Confidence Score: [0-100]
        4. Explanation: A 2-sentence breakdown.
        """
        
        # Direct call without the complex loops
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, img]
        )
        
        if response.text:
            return response.text
        return "RealityLens received an empty response from AI."

    except Exception as e:
        error_msg = str(e)
        # Friendly check for the 429 quota error
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "RealityLens: Quota exceeded. Please wait 60 seconds and try again."
        return f"AI Error: {error_msg}"