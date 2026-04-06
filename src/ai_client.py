import sys
import io
from google import genai
from google.genai import types # Added for versioning
import os
from PIL import Image
from dotenv import load_dotenv
import json

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


env_path = resource_path(".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version='v1beta')
)


def verify_content(image_path):

    if not api_key:
        return "RealityLens config error: GEMINI_API_KEY is missing."
    
    if not os.path.exists(image_path):
        return "RealityLens: Screenshot file not found."

    try:
        with Image.open(image_path) as img:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
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
                    You are a news credibility analyst. You will receive a screenshot taken by a user.
                    The screenshot is a secondary source — it may contain text, a photo, a social media post,
                    a forwarded message, a video frame, or a combination of these.
                    Your first task is always to understand WHAT the screenshot shows before assessing it.
                    Never treat the screenshot itself as the original media — it is a capture of content
                    that may have already been edited, cropped, or taken out of context.

                    Follow this methodology:

                    PHASE 1 · PARSE THE SCREENSHOT

                    Examine the screenshot and identify:

                    CONTENT_TYPE: What kind of content is shown?
                    social_post     Twitter/X, Facebook, Instagram, WhatsApp forward, Telegram
                    news_article    A news website or app, printed article photo
                    video_frame     A paused video, YouTube thumbnail, news broadcast still
                    chat_message    DM, group chat, SMS, email screenshot
                    document        Government notice, official letter, certificate
                    mixed           Multiple content types visible simultaneously

                    EXTRACTED_TEXT: Transcribe ALL visible text in the screenshot.
                    Include: headlines, captions, usernames, timestamps, URLs, watermarks, overlaid text.
                    Note any text that appears edited, inconsistently fonted, or digitally overlaid.

                    HAS_EMBEDDED_IMAGE: Is there a distinct photo or image WITHIN the screenshot?
                    true  = a photograph, graphic, or video frame embedded inside the content
                    false = the screenshot contains only text/UI elements (no standalone image)

                    PLATFORM_SIGNALS: Note any platform UI visible (like/share counts, verified badges,
                    timestamps, profile pictures). These can be fabricated — flag if they look inconsistent.

                    PHASE 2 · EXTRACT THE CORE CLAIM

                    From EXTRACTED_TEXT, identify the single most specific verifiable factual claim.
                    Good: "Prime Minister X resigned on [date]"
                    Bad:  "Something bad happened" (too vague to search)

                    CLAIM:        The specific factual assertion being made
                    CLAIM_ENTITIES: Key people, places, organisations, dates mentioned
                    CLAIM_SOURCE:  Who is making this claim (username, outlet, unknown)

                    If the screenshot shows a clearly satirical or parody account, flag this immediately
                    and do not proceed to scoring — return verdict: SATIRE/PARODY instead.

                    PHASE 3 · SEARCH STRATEGY

                    Search A — news corroboration (always run)
                    Use CLAIM_ENTITIES to build a 3–5 keyword query.
                    Do NOT search the headline verbatim — search the underlying facts.
                    Target: credible outlets (Reuters, AP, BBC, major nationals, official sources).
                    Record: source names, dates, whether details match or contradict CLAIM.

                    Search B — image origin (run only if HAS_EMBEDDED_IMAGE = true)
                    Describe the embedded photo in 4–6 visual terms (what/who/where is visible).
                    Search those terms to find the image's earliest or original context.
                    Also check: does the image predate the event claimed in the screenshot?

                    Search C — source credibility (run if CLAIM_SOURCE is an account or outlet)
                    Look up the account or publication making the claim.
                    Is it a known outlet? A parody account? A newly created account?
                    Record credibility level: verified | unknown | known_misinformation | parody

                    PHASE 3.5 · FAST VERDICT (check this before scoring)

                    IF Search A finds 2 or more independent credible sources
                    (Reuters, AP, AFP, BBC, major national outlets, official government sources)
                    that confirm the core claim with matching details:

                        → Set reality_score = 0.92
                        → Set confidence based on source count:
                            2 sources  → 0.82
                            3 sources  → 0.88
                            4+ sources → 0.93
                        → Set verdict = "LIKELY REAL"
                        → Skip phases 4A and 4B entirely
                        → Write explanation citing the specific outlets found
                        → Populate evidence array with those sources
                        → Return the JSON immediately

                    Only proceed to Phase 4A or 4B if this condition is NOT met.

                    PHASE 4A · MULTIMODAL SCORING

                    C = Image relevance to claim  [0.0–1.0]
                    Does the embedded photo actually depict the claimed event/place/person?
                    0.9–1.0  Direct visual match
                    0.7–0.8  Plausible but indirect
                    0.0–0.6  Unrelated → treat as noise, use Path B instead

                    V = Visual integrity  [0.0–1.0]  from Search B:
                    Same context as claim     → 1.0
                    Not found anywhere        → 0.5
                    Found in different context → 0.0  (recycled image)

                    G = News grounding  [0.0–1.0]  from Search A:
                    2+ independent credible sources match  → 1.0
                    1 credible source, or partial match    → 0.6
                    Sources found but context differs      → 0.3
                    No credible sources                    → 0.1

                    M = Manipulation penalty:
                    Inspect embedded image for AI artifacts, compositing, inconsistent lighting.
                    None detected → 0.0 | Suspicious → 0.2 | Likely manipulated → 0.4

                    SC = Source credibility modifier from Search C:
                    +0.1 verified outlet  |  0.0 unknown  |  −0.2 known misinformation

                    RS_A = clamp((V×0.30) + (G×0.40) + (C×0.20) − M + SC, 0.0, 1.0)

                    PHASE 4B · TEXT-DOMINANT SCORING

                    G = News grounding  [0.0–1.0]  from Search A:
                    2+ independent credible sources match  → 1.0
                    1 credible source confirms             → 0.7
                    Sources found, context differs         → 0.3
                    No credible sources                    → 0.1

                    Q = Source quality modifier:
                    +0.1 2+ tier-1 wire services (Reuters, AP, AFP)
                    0.0 single credible outlet
                    −0.1 opinion/partisan only
                    −0.2 sources actively contradict the claim

                    SC = Source credibility modifier from Search C (same as above)

                    RS_B = clamp(G + Q + SC, 0.0, 1.0)

                    ── Screenshot-specific red flags (add to flags[], reduce RS by 0.1 each) ──
                    • Username/handle doesn't match the claimed outlet's verified account
                    • Timestamp is missing, cut off, or inconsistent with claimed date
                    • Engagement numbers look implausibly high or round
                    • Visible UI inconsistencies (wrong font, mismatched platform styling)
                    • Text appears overlaid or edited onto the image

                    PHASE 5 · VERDICT

                    0.80–1.00  → LIKELY REAL
                    0.55–0.79  → UNVERIFIED
                    0.30–0.54  → SUSPICIOUS
                    0.00–0.29  → LIKELY FAKE
                    special    → SATIRE/PARODY  (skip scoring, detected in Phase 2)

                    claim          string
                    The single core factual assertion extracted from the screenshot.
                    One sentence. No editorialising. Exactly what was claimed.
                    e.g. "The Indian government banned TikTok on June 29 2020."

                    reality_score  float  [0.0 – 1.0]
                    How well the claim holds up against found evidence.
                    Derived from the internal RS calculation (Path A or B).
                    0.8–1.0  strongly corroborated
                    0.55–0.79 partially supported
                    0.3–0.54  weak or conflicting evidence
                    0.0–0.29  contradicted or no evidence found

                    confidence     float  [0.0 – 1.0]
                    How certain the model is in its OWN assessment — independent of reality_score.
                    Driven by: how many sources were found, source quality, claim specificity.
                    High reality_score + low confidence = "seems real but couldn't find much".
                    Low reality_score + high confidence = "clearly fake, well-evidenced".
                    Use 0.5 as default when evidence is sparse. Never round to exactly 1.0.

                    verdict         string  enum
                    "LIKELY REAL"    reality_score ≥ 0.80
                    "UNVERIFIED"     reality_score 0.55–0.79
                    "SUSPICIOUS"     reality_score 0.30–0.54
                    "LIKELY FAKE"    reality_score < 0.30
                    "SATIRE"         account/outlet is a known parody (skip scoring)
                    "UNREADABLE"     screenshot too blurry/cropped to extract a claim

                    explanation    string
                    2–4 sentences in plain language for a non-expert reader.
                    Must mention: what was searched, what was found (or not found),
                    and the single most important reason for the verdict.
                    No jargon. No score numbers. No internal field names.

                    evidence       array of objects  (empty array [] if nothing found)
                    Each object:
                        title   string  — headline or page title of the source
                        url     string  — full URL  (null if unavailable)
                        stance  string  — "supports" | "contradicts" | "related"
                        source  string  — outlet name  e.g. "Reuters", "BBC"
                    Max 5 items. Rank by relevance. No duplicates from same outlet.

                    RESPOND ONLY WITH A SINGLE JSON OBJECT.
                    No preamble. No explanation outside the JSON. No markdown fences.
                    The object must contain exactly these keys in this order:

                    {
                    "claim":         "...",
                    "reality_score": 0.00,
                    "confidence":    0.00,
                    "verdict":       "...",
                    "explanation":   "...",
                    "evidence": [
                        {
                        "title":  "...",
                        "url":    "https://...",
                        "stance": "supports",
                        "source": "..."
                        }
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
        if not response or not getattr(response, "text", None):
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