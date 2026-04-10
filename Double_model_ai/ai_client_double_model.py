import sys
import io
import time
import os
import json
import random
import requests
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

# Replace brave_api_key line with:



current_situation = "Please wait while we analyze the capture..."

def _set_current_situation(message, on_status=None):
    global current_situation
    current_situation = message
    if on_status:
        on_status(message)


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)

env_path = resource_path(".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
api_keys = os.getenv("GEMINI_API_KEY", "").split(",")
api_keys = [k.strip() for k in api_keys if k.strip()]
groq_api_key = os.getenv("GROQ_API_KEY", "").strip()


GROQ_MODELS = [
    "llama-3.3-70b-versatile",        # Best quality, large context
    "moonshotai/kimi-k2-instruct",    # Strong reasoning, huge context
    "qwen/qwen3-32b",                 # Good at structured JSON output
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Fast fallback
    "llama-3.1-8b-instant",           # Last resort, very fast
]

MODELS = [
    "gemini-2.5-flash",
]

# ── Phase 1: Extract claim + image description from screenshot ──────────────

EXTRACTION_PROMPT = """
You are a visual analyst. Examine this screenshot and extract structured information.

if the screenshot is unreadable, blurry, or too cropped to understand, set claim to "UNREADABLE" and leave other fields blank or false.

Return ONLY a JSON object with these exact keys:

{
  "content_type": "social_post | news_article | video_frame | chat_message | document | mixed",
  "extracted_text": "all visible text in the screenshot",
  "claim": "the single most specific verifiable factual claim in one sentence",
  "claim_entities": "key people, places, organisations, dates as a comma-separated string",
  "claim_source": "who is making the claim (username, outlet, or unknown)",
  "has_embedded_image": true or false,
  "image_description": "if has_embedded_image is true: describe the photo in 6-8 visual terms for reverse searching. Otherwise: null",
  "is_satire": true or false
}

Rules:
- Output ONLY JSON, no markdown, no commentary
- If the screenshot is unreadable or too blurry, set claim to "UNREADABLE"
- Only mark is_satire true if the account is clearly labeled satire or parody
-if is_satire is true, set claim to the core claim but also include "This content appears to be from a satire or parody account. The claim should not be taken as factual news." in the explanation field, and set reality_score to 0.00, confidence to 0.95, and verdict to "SATIRE". Leave evidence empty.
"""

# ── Phase 2: Score and verdict based on search results ──────────────────────

def build_scoring_prompt(extraction, search_results_text):
    return f"""
You are a news credibility analyst. Based on the extracted claim and search results below, produce a verdict.

EXTRACTED INFORMATION:
- Claim: {extraction.get('claim')}
- Content Type: {extraction.get('content_type')}
- Source: {extraction.get('claim_source')}
- Has Embedded Image: {extraction.get('has_embedded_image')}
- Image Description: {extraction.get('image_description')}

SEARCH RESULTS:
{search_results_text}

SCORING RULES:

News grounding G [0.0-1.0]:
2+ independent credible sources match → 1.0
1 credible source confirms → 0.7
Sources found, context differs → 0.3
No credible sources → 0.1

IF Search finds 2 or more independent credible sources
(Reuters, AP, AFP, BBC, major national outlets, official government sources)
that confirm the core claim with matching details:

    → Set reality_score = 0.92
    → Set confidence based on source count:
        2 sources  → 0.82
        3 sources  → 0.88
        4+ sources → 0.93
    → Set verdict = "LIKELY REAL"
    → Write explanation citing the specific outlets found
    → Populate evidence array with those sources
    → Return the JSON immediately

Source quality Q:
+0.1 two or more tier-1 wire services (Reuters, AP, AFP)
0.0 single credible outlet
-0.1 opinion or partisan only
-0.2 sources actively contradict the claim

Source credibility SC:
+0.1 verified outlet
0.0 unknown
-0.2 known misinformation source

Final score = clamp(G + Q + SC, 0.0, 1.0)

Verdict thresholds:
0.80-1.00 → LIKELY REAL
0.55-0.79 → UNVERIFIED
0.30-0.54 → SUSPICIOUS
0.00-0.29 → LIKELY FAKE

Red flags (subtract 0.1 each):
- Username does not match verified account
- Timestamp missing or inconsistent
- Engagement numbers implausibly high
- UI inconsistencies visible
- Text appears overlaid or edited

Return ONLY this JSON object:

{{
  "claim": "the core factual claim in one sentence",
  "reality_score": 0.00,
  "confidence": 0.00,
  "verdict": "LIKELY REAL | UNVERIFIED | SUSPICIOUS | LIKELY FAKE | SATIRE | UNREADABLE",
  "explanation": "2-4 sentences in plain language mentioning what was searched, what was found, and the main reason for the verdict",
  "evidence": [
    {{
      "title": "...",
      "url": "...",
      "stance": "supports | contradicts | related",
      "source": "outlet name"
    }}
  ]
}}

Rules:
- Max 5 evidence items
- Output ONLY JSON, no markdown, no commentary
- confidence is how certain YOU are, independent of reality_score
- Never round confidence to exactly 1.0
"""


def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


def call_gemini(prompt, image_part=None, api_keys=api_keys, keys_to_try=None):
    """Try each key and model until one works. Returns parsed text or raises."""
    if keys_to_try is None:
        keys_to_try = api_keys[:]
        random.shuffle(keys_to_try)

    MAX_RETRIES = 2
    MAX_TOTAL_SECONDS = 45
    start_time = time.time()
    last_error = "All API keys exhausted."

    i = 0
    while i < len(keys_to_try):
        key = keys_to_try[i]
        key_exhausted = False
        
        for model in MODELS:
            for attempt in range(MAX_RETRIES):
                if time.time() - start_time > MAX_TOTAL_SECONDS:
                    return None, "Service timeout. Please try again."

                try:
                    client = get_gemini_client(key)
                    contents = [prompt, image_part] if image_part else [prompt]

                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                    )

                    if not response or not getattr(response, "text", None):
                        last_error = "Empty response from AI."
                        break

                    raw = response.text.strip()
                    if raw.startswith("```json"):
                        raw = raw.replace("```json", "", 1).replace("```", "", 1).strip()
                    elif raw.startswith("```"):
                        raw = raw.replace("```", "", 2).strip()

                    return raw, None

                except Exception as e:
                    err = str(e)
                    if "429" in err or "RESOURCE_EXHAUSTED" in err:
                        print(f"⚠️ Quota exhausted on {model}, removing key and trying next...")
                        last_error = "Quota exhausted."
                        # Mark key as exhausted and remove it so subsequent calls skip it
                        keys_to_try.pop(i)
                        key_exhausted = True
                        break
                    elif "503" in err or "UNAVAILABLE" in err:
                        if attempt < MAX_RETRIES - 1:
                            wait = 5 * (attempt + 1)
                            print(f"⚠️ {model} overloaded, retrying in {wait}s...")
                            time.sleep(wait)
                        else:
                            print(f"⚠️ {model} still failing, next model...")
                            last_error = f"{model} unavailable."
                            break
                    else:
                        print(f"⚠️ Error on {model}: {err}")
                        last_error = f"AI Error: {err}"
                        break
            
            if key_exhausted:
                break  # Exit model loop, don't increment i
        
        if not key_exhausted:
            i += 1  # Only increment if key was not exhausted

    return None, last_error

def call_groq(prompt):
    """Call Groq API with the given prompt. Returns response text or raises."""
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing.")
    

    client = Groq(api_key=groq_api_key)
    for model in GROQ_MODELS:
        try:
            print(f"🤖 Scoring with Groq {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temp for consistent structured output
                max_tokens=1500,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw.replace("```json", "", 1).replace("```", "", 1).strip()
            elif raw.startswith("```"):
                raw = raw.replace("```", "", 2).strip()

            return raw, None

        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err.lower():
                print(f"⚠️ Groq rate limit on {model}, trying next...")
                continue
            else:
                print(f"⚠️ Groq error on {model}: {err}")
                continue

    return None, "All Groq models failed."


def tavily_search(query, num_results=5):
    """Search using Tavily API. Returns list of result dicts."""
    if not tavily_api_key:
        print("⚠️ No Tavily API key found, skipping search.")
        return []

    try:
        client = TavilyClient(api_key=tavily_api_key)

        response = client.search(
            query=query,
            max_results=num_results,
            search_depth="basic",  # use "advanced" for better results but costs 2 credits
            include_answer=True,   # Tavily gives a pre-summarized answer too
        )   

        results = []

        # Tavily gives a direct answer summary — prepend it as a result
        if response.get("answer"):
            results.append({
                "title": "Tavily Summary",
                "url": "",
                "description": response["answer"],
                "source": "Tavily AI Summary",
            })

        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", ""),
                "source": item.get("url", "").split("/")[2] if item.get("url") else "Unknown",
            })

        return results

    except Exception as e:
        print(f"⚠️ Tavily search failed: {e}")
        return []

def format_search_results(results):
    """Format search results into a readable string for the scoring prompt."""
    if not results:
        return "No search results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['source']}: {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   Summary: {r['description']}")
        lines.append("")
    return "\n".join(lines)


def verify_content(image_path, on_status=None):
    if not api_keys:
        return "RealityLens config error: GEMINI_API_KEY is missing."

    if not os.path.exists(image_path):
        return "RealityLens: Screenshot file not found."

    # ── Load and compress image ──────────────────────────────────────────────
    try:
        with Image.open(image_path) as img:
            _set_current_situation("Loading and compressing image...", on_status)
            if img.width > 1280 or img.height > 1280:
                img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            img = img.convert("RGB")
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG", quality=85)
            img_bytes = img_byte_arr.getvalue()
            print(f"📦 Image size: {len(img_bytes) / 1024:.1f} KB")

            _set_current_situation("Image loaded and compressed.", on_status)
    except Exception as e:
        return f"RealityLens: Failed to read image — {e}"

    image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

    # Initialize key rotation list once for all API calls in this verification
    keys_to_try = api_keys[:]
    random.shuffle(keys_to_try)

    # ── Phase 1: Extract claim from screenshot ───────────────────────────────
    print("🔍 Phase 1: Extracting claim from screenshot...")
    _set_current_situation("Extracting information from screenshot...", on_status)
    raw_extraction, err = call_gemini(EXTRACTION_PROMPT, image_part, keys_to_try=keys_to_try)
    if err:
        return f"RealityLens: Extraction failed — {err}"

    try:
        extraction = json.loads(raw_extraction)
    except json.JSONDecodeError:
        return {"error": "Failed to parse extraction response", "raw": raw_extraction}

    claim = extraction.get("claim", "")

    if extraction.get("is_satire"):
        return {
            "claim": claim,
            "reality_score": 0.00,
            "confidence": 0.95,
            "verdict": "SATIRE",
            "explanation": "This content appears to be from a satire or parody account. The claim should not be taken as factual news.",
            "evidence": []
        }

    if claim == "UNREADABLE" or not claim:
        return {
            "claim": "Unable to extract a claim.",
            "reality_score": 0.00,
            "confidence": 0.1,
            "verdict": "UNREADABLE",
            "explanation": "The screenshot was too blurry, cropped, or unclear to extract a verifiable claim.",
            "evidence": []
        }

    # ── Phase 2: Search for the claim ────────────────────────────────────────
    print(f"🌐 Phase 2: Searching for — {claim}")
    _set_current_situation("Searching for relevant information...", on_status)
    entities = extraction.get("claim_entities", claim)
    search_query = entities if entities else claim
    
    search_results = tavily_search(search_query)

    if extraction.get("has_embedded_image") and extraction.get("image_description"):
        print(f"🖼️ Searching for image origin...")
        _set_current_situation("Searching for image origin...", on_status)
        image_results = tavily_search(extraction["image_description"], num_results=3)
        search_results += image_results

    search_text = format_search_results(search_results)
    print(f"📰 Found {len(search_results)} search results")

    # ── Phase 3: Score and verdict ───────────────────────────────────────────
    print("🧠 Phase 3: Scoring and generating verdict...")
    _set_current_situation("Scoring and generating verdict...", on_status)
    scoring_prompt = build_scoring_prompt(extraction, search_text)
    raw_verdict, err = call_groq(scoring_prompt)
    if err:
        print(f"⚠️ Groq failed ({err}), falling back to Gemini for scoring...")
        raw_verdict, err = call_gemini(scoring_prompt)
        if err:
            return f"RealityLens: Scoring failed — {err}"

    try:
        result = json.loads(raw_verdict)
        print(result)
        return result
    except json.JSONDecodeError:
        print("❌ JSON Parse Error:", raw_verdict)
        return {"error": "AI failed to return valid JSON", "raw": raw_verdict}