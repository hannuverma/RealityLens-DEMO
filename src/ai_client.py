import sys
import io
from google import genai
from google.genai import types # Added for versioning
import os
from PIL import Image
from dotenv import load_dotenv
import json

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
    http_options=types.HttpOptions(api_version='v1beta')
)


def verify_content(image_path):

    if not api_key:
        return "RealityLens config error: GEMINI_API_KEY is missing."

    try:
        img = Image.open(image_path)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        # 2. Create the Part object (This is the most stable way)
        image_part = types.Part.from_bytes(
            data=img_bytes,
            mime_type="image/png"
        )
        # This is the exact string confirmed by your doctor.py output
        model_name = "gemini-2.5-flash" 
        search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
            

        config = types.GenerateContentConfig(
            tools = [search_tool],  # Assuming search_tool is defined elsewhere
        )

        prompt = """
                    You are an AI forensic fact-checking engine used in a misinformation detection system called RealityLens.

                    Your job is to analyze the provided image and determine whether the implied claim is real, misleading, or fake.

                    Follow this methodology:

                    1. Identify the central claim suggested by the image.
                    2. Use Google Search to verify whether credible sources report the same event.
                    3. Check whether the image has appeared earlier in a different context (reverse image reasoning).
                    4. Compare coverage across multiple reliable sources.

                    Calculate the Reality Score (RS):

                    RS = 0.4 * R + 0.3 * T + 0.3 * C

                    Where:
                    R = Source reliability score (0–1)
                    T = Temporal consistency score (0–1)
                    C = Cross-source consensus score (0–1)

                    Interpretation:
                    RS > 0.75 → Likely Real  
                    0.40–0.75 → Suspicious / Needs verification  
                    RS < 0.40 → Likely Fake

                    Return your answer ONLY as valid JSON with the following schema:

                    {
                    "claim": "string",
                    "scores": {
                        "source_reliability": number,
                        "temporal_consistency": number,
                        "consensus": number
                    },
                    "reality_score": number,
                    "confidence": number,
                    "verdict": "Likely Real | Suspicious | Likely Fake",
                    "explanation": "short explanation for the user",
                    "evidence": [
                        {"title": "string", "url": "string"},
                        {"title": "string", "url": "string"}
                    ]
                    }

                    Rules:
                    - Do not include markdown
                    - Do not include commentary
                    - Output ONLY JSON
                    """
        
        # Direct call without the complex loops
        print(f"🤖 Sending content to AI for analysis...")
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, image_part],
            config=config
        )
        
        # 2. Add safety check for empty response
        if not response.text:
            return "RealityLens: AI returned an empty response."

        # 3. Clean the response (sometimes AI adds ```json ... ``` tags)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1).replace("```", "", 1).strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 2).strip()

        try:
            result = json.loads(raw_text)
            print(result)
            return result
        except json.JSONDecodeError:
            print("❌ JSON Parse Error. Raw text follows:")
            print(raw_text)
            return {"error": "AI failed to return valid JSON", "raw": raw_text}
        

    except Exception as e:
        error_msg = str(e)
        # Friendly check for the 429 quota error
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "RealityLens: Quota exceeded. Please wait 60 seconds and try again."
        return f"AI Error: {error_msg}"