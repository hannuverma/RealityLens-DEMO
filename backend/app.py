import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
import sys
import io
import time
import requests
import os
import json
import random
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64


current_situation = "This version is no longer working please switch to the latest version"

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
You are a visual analyst and claim extractor. Examine this screenshot carefully.

if the screenshot is unreadable, blurry, or too cropped to understand, set claim to "UNREADABLE" and leave other fields blank or false.

STEP 1 — IDENTIFY CONTENT TYPE
What kind of content is shown?
- social_post: Twitter/X, Facebook, Instagram, WhatsApp, Telegram
- news_article: news website, app, printed article
- video_frame: paused video, YouTube thumbnail, broadcast still
- chat_message: DM, group chat, SMS, email
- document: government notice, official letter, certificate
- mixed: multiple types visible

STEP 2 — EXTRACT ALL TEXT
Transcribe every piece of visible text including:
- Headlines, captions, post text
- Usernames, handles, verified badges
- Timestamps, dates
- Hashtags (these are CRITICAL context clues — always include them)
- URLs, watermarks, overlaid text
- Video duration markers, view counts

STEP 3 — IDENTIFY THE REAL CLAIM
The claim is NOT always the literal quote in the post.
Ask yourself: "What is this post trying to make people believe?"

Examples:
- A soldier crying + hashtags #Iran #Israel → claim is about the Iran-Israel conflict, not the quote
- A photo of a politician + caption "caught stealing" → claim is about the politician stealing
- A video thumbnail + "BREAKING" → claim is the breaking news event

For social posts specifically:
- Hashtags reveal the TRUE context — use them to understand what event is being referenced
- The implied claim (what the post wants you to believe) matters more than the literal text
- An emotional video posted with war hashtags = claim is about that war, not about the emotion

STEP 4 — BUILD SEARCH ENTITIES
Extract the most searchable facts:
- Real names of people (not "an American soldier" — look for name tags, captions, any ID)
- Specific locations if visible
- Dates and timestamps
- Event names from hashtags (e.g. #IranMassacre → Iran conflict 2024)
- Organisation names
- If a person is unidentified, use their role + context (e.g. "US soldier Iran Israel conflict 2025")

STEP 5 — DESCRIBE EMBEDDED IMAGE FOR REVERSE SEARCH
If there is a photo or video frame embedded:
- Describe WHO is in it (appearance, uniform, identifying features)
- Describe WHERE it appears to be (desert, urban, indoors)
- Describe WHAT is happening
- Note any vehicles, flags, insignia, text overlays
- Note the emotional tone
These details are used to reverse-search the image origin.

Return ONLY a JSON object with these exact keys:

{
  "content_type": "social_post | news_article | video_frame | chat_message | document | mixed",
  "extracted_text": "full verbatim transcription of all visible text including hashtags",
  "claim": "the implied factual assertion this content is making — what it wants viewers to believe — in one specific sentence",
  "claim_entities": "optimised search query using the most specific facts: names, places, events, dates, hashtag context — written as a search engine query not a list",
  "claim_source": "username or outlet making the claim, note if unverified/no blue tick",
  "has_embedded_image": true or false,
  "image_description": "detailed 6-8 term visual description for reverse image searching: who, where, what, uniform details, background, emotional state. null if no embedded image.",
  "is_satire": true or false
}

ANTI-VAGUE CLAIM RULES:
- NEVER extract a claim like "X conflict is bad/harmful/causing distress" — this is an opinion, not a verifiable fact
- NEVER extract a claim that is so broad it would always be true
- The claim must be specific enough that it could be TRUE or FALSE
- For emotional social posts, the claim is about the VIDEO/IMAGE being real and from the stated context
  e.g. "This video shows a real US soldier crying in the Iran-Israel conflict zone in April 2025"
  NOT "The Iran-Israel conflict is causing distress"
- If the post is presenting a VIDEO as evidence of something, the claim is:
  "This [video/image] authentically depicts [what it claims to show] in [the context implied by hashtags/caption]"
- A claim about a specific person's emotional state in a specific conflict zone IS verifiable
  (the video either is real footage from that context or it isn't)

Rules:
- Output ONLY JSON, no markdown, no commentary
- claim_entities should read like a Google search query e.g. "US soldier crying video Iran Israel war 2025" not "soldier, Iran, Israel, 2025"
- If hashtags are present, they MUST inform the claim and claim_entities
- Only mark is_satire true if clearly labeled as parody/satire
- Never use vague claims like "something happened" — be specific about what is being implied
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

    ════════════════════════════════════════
    STEP 1 — CRITICAL CHECKS (run these FIRST, return immediately if triggered)
    ════════════════════════════════════════

    PRIORITY CHECK · CREDIBLE NEWS CORROBORATION (run this BEFORE all image checks)
    IF 2+ independent credible sources (Reuters, AP, AFP, BBC, Al Jazeera, Guardian,
    NYT, Washington Post, official .gov or .mil sites, established national newspapers)
    confirm the core claim with matching details:
    → reality_score = 0.92
    → confidence: 2 sources → 0.82 | 3 sources → 0.88 | 4+ sources → 0.93
    → verdict = "LIKELY REAL"
    → Cite the specific outlets found in explanation
    → STOP. Return JSON immediately.
    → NOTE: Even if the image is AI-generated or stock footage, if the underlying
    news claim is verified by credible sources, the claim is LIKELY REAL.
    The image quality does not invalidate a well-reported news event.

    Only proceed to image checks below if the priority check did NOT trigger.

    CHECK 1 · STOCK PHOTO/VIDEO
    Scan search results for: Adobe Stock, Getty Images, Shutterstock, iStock,
    Alamy, Pond5, Depositphotos, or words like "stock photo", "stock video",
    "stock footage", "concept video", "royalty free".
    IF FOUND AND no credible news corroboration exists:
    → reality_score = 0.10, confidence = 0.92, verdict = "LIKELY FAKE"
    → Explanation: state clearly the image is staged stock footage, not a real event
    → STOP. Return JSON immediately.

    CHECK 2 · VIRAL SOCIAL MEDIA WITH ZERO NEWS COVERAGE
    IF ALL of these are true:
    - Claim source is unverified social media account (no blue tick / not a known outlet)
    - Search results contain ONLY social media: YouTube, Instagram, Facebook, TikTok, Twitter/X
    - Zero results from credible sources (as defined in STEP 2)
    - Content is emotionally charged (war, tragedy, disaster, outrage, shocking)
    THEN:
    → reality_score = 0.15, confidence = 0.85, verdict = "LIKELY FAKE"
    → Explanation: state unverified source, zero credible news coverage, viral spread
    on social media is NOT evidence of authenticity — it is a red flag
    → STOP. Return JSON immediately.

    CHECK 3 · RECYCLED OR OUT-OF-CONTEXT IMAGE
    If search results show the embedded image was used in a DIFFERENT context,
    a DIFFERENT time period, or a DIFFERENT location than claimed:
    → Apply -0.4 penalty to final score
    → Flag clearly in explanation
    → NOTE: Only apply this if the news claim itself is also unverified.
    A real news event may use a representative or archival image.

    CHECK 4 · UNVERIFIED SOURCE, NO CORROBORATION
    If claim source is an unverified social account AND no credible outlet reported it:
    → Apply -0.1 penalty to final score

    ════════════════════════════════════════
    STEP 2 — CREDIBLE SOURCE DEFINITION
    ════════════════════════════════════════

    CREDIBLE (count toward grounding):
    Reuters, AP, AFP, BBC, Al Jazeera, The Guardian, NYT, Washington Post,
    official government sites (.gov, .mil), established national newspapers

    NOT CREDIBLE (do not count as evidence):
    YouTube, Instagram, Facebook, TikTok, Twitter/X, Reddit,
    forums, blogs, unknown websites, Tavily AI Summary alone

    ════════════════════════════════════════
    STEP 3 — SCORING (only if no critical check triggered)
    ════════════════════════════════════════

    News grounding G [0.0-1.0]:
    2+ independent credible sources exact match → 1.0
    1 credible source confirms → 0.7
    Sources found but context differs → 0.3
    No credible sources → 0.0

    Source quality Q:
    +0.1 two or more tier-1 wire services (Reuters, AP, AFP)
    0.0 single credible outlet
    -0.1 opinion or partisan sources only
    -0.2 sources actively contradict the claim

    Source credibility SC:
    +0.1 verified outlet
    0.0 unknown
    -0.2 known misinformation source

    Final score = clamp(G + Q + SC, 0.0, 1.0)

    Additional red flags (subtract 0.1 each):
    - Username does not match verified account
    - Timestamp missing or inconsistent
    - Engagement numbers implausibly high or round
    - UI inconsistencies (wrong font, mismatched platform styling)
    - Text appears overlaid or digitally edited onto image
    - Social media only results with no news coverage

    ════════════════════════════════════════
    STEP 4 — VERDICT THRESHOLDS
    ════════════════════════════════════════

    0.80 – 1.00 → LIKELY REAL
    0.55 – 0.79 → UNVERIFIED
    0.30 – 0.54 → SUSPICIOUS
    0.00 – 0.29 → LIKELY FAKE

    ════════════════════════════════════════
    OUTPUT — return ONLY this JSON, no markdown, no commentary
    ════════════════════════════════════════

    {{
    "claim": "the core factual claim in one sentence",
    "reality_score": 0.00,
    "confidence": 0.00,
    "verdict": "LIKELY REAL | UNVERIFIED | SUSPICIOUS | LIKELY FAKE | SATIRE | UNREADABLE",
    "explanation": "2-4 sentences in plain language: what was searched, what was found, main reason for verdict. If stock footage or viral misinformation pattern detected, say so explicitly. If credible sources confirm the claim, cite them by name.",
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
    - Max 5 evidence items, ranked by relevance
    - Output ONLY JSON, no markdown, no commentary
    - confidence = how certain YOU are, independent of reality_score
    - Never round confidence to exactly 1.0
    - Social media results in evidence should be marked "related" not "supports"
    - Stock footage or AI image does not affect verdict if claim is news-verified
    """
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

def call_groq_vision(prompt, image_bytes):
    """Groq vision fallback for extraction when Gemini fails."""
    if not groq_api_key:
        return None, "GROQ_API_KEY is missing."

    import base64
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    groq_client = Groq(api_key=groq_api_key)

    # Only these Groq models support vision
    vision_models = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
    ]

    for model in vision_models:
        try:
            print(f"🔍 Extracting with Groq vision {model}...")
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                temperature=0.1,
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
            print(f"⚠️ Groq vision error on {model}: {err}")
            continue

    return None, "All Groq vision models failed."

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

def call_kimi(prompt, image_bytes=None):
    ACCOUNT_ID = os.getenv("ACCOUNT_ID", "").strip()
    AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN", "").strip()
    
    # Note: image_bytes should be the raw bytes from img_bytes in verify_content
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/moonshotai/kimi-k2.5"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

    # Construct the content list
    content = [{"type": "text", "text": prompt}]
    
    if image_bytes:
        # Encode bytes to base64 string
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"messages": [{"role": "user", "content": content}]}
        )
        
        # Check for Cloudflare success
        res_json = response.json()
        if not res_json.get("success"):
            return None, f"Cloudflare Error: {res_json.get('errors')}"
            
        raw = res_json["result"]["response"].strip()
        
        # Clean up Markdown formatting if present
        if raw.startswith("```json"):
            raw = raw.replace("```json", "", 1).replace("```", "", 1).strip()
        elif raw.startswith("```"):
            raw = raw.replace("```", "", 2).strip()

        return raw, None

    except Exception as e:
        return None, f"Kimi-K2 Connection Error: {str(e)}"

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

def parallel_search(query, num_results=5):
    parallel_key = os.getenv("PARALLEL_API_KEY", "").strip()
    if not parallel_key:
        print("⚠️ No Parallel API key found, skipping search.")
        return []

    try:
        response = requests.post(
            "https://api.parallel.ai/v1beta/search",
            headers={
                "Content-Type": "application/json",
                "x-api-key": parallel_key,
            },
            json={
                "objective": f"Find credible news sources that confirm or deny this claim: {query}",
                "search_queries": [query],
                "mode": "fast",        # fast = <5s, quality = better but slower
                "max_results": num_results,
                "excerpts": {
                    "max_chars_per_result": 1500  # enough context for scoring
                }
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            domain = item.get("url", "").split("/")[2] if item.get("url") else "Unknown"
            excerpts = item.get("excerpts", [])
            description = " ".join(excerpts) if excerpts else ""
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": description,
                "source": domain,
                "publish_date": item.get("publish_date", ""),
            })

        return results

    except Exception as e:
        print(f"⚠️ Parallel search failed: {e}")
        return []

def format_search_results(results):
    if not results:
        return "No search results found."

    lines = []
    for i, r in enumerate(results, 1):
        date = f" ({r.get('publish_date', 'date unknown')})" if r.get('publish_date') else ""
        lines.append(f"{i}. {r['source']}{date}: {r['title']}")
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
    #raw_extraction, err = call_gemini(EXTRACTION_PROMPT, image_part, keys_to_try=keys_to_try)
    raw_extraction, err = call_groq_vision(EXTRACTION_PROMPT, img_bytes)
    if err:
        print(f"⚠️ Groq failed ({err}), trying Gemini vision...")
        _set_current_situation("AI unavailable, trying backup...", on_status)
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

    try:    
        search_results = tavily_search(search_query, num_results=5)
    except Exception as e:
        if "API key" in str(e):
            print(f"⚠️ Tavily search failed due to API key issue: {e}")
            search_results = parallel_search(search_query)
        else:
            print(f"⚠️ Tavily search error: {e}")
            search_results = parallel_search(search_query)

    if extraction.get("has_embedded_image") and extraction.get("image_description"):
        print("🖼️ Searching for image origin...")
        _set_current_situation("Searching for image origin...", on_status)
        try:
            image_results = parallel_search(extraction["image_description"], num_results=3)
        except Exception as e:
            print(f"⚠️ Image search error: {e}")
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


app = FastAPI(title="RealityLens Backend")

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Thread pool for running blocking analysis
executor = ThreadPoolExecutor(max_workers=3)

@app.get("/status")
async def status_endpoint():
    """Return the current analysis status."""
    return {"current_situation": current_situation}


@app.post("/ai_client")
async def ai_client_endpoint(file: UploadFile = File(...)):
    # 1. Create a safe path for the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # 2. Efficiently save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Run verify_content in thread pool to keep it async
        # This allows the /status endpoint to be polled while analysis runs
        global executor 
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, verify_content, file_path)

        return result

    except Exception as e:
        # Log the error for debugging
        print(f"❌ Server Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    finally:
        # 4. Cleanup: Always remove the file after the response is sent
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/health_check")
async def health_check():
    return {"status": "healthy"}

# To run this: uvicorn server:app --host 0.0.0.0 --port 8000 --reload