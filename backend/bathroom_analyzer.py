import json
import os
import random
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Use a slightly less congested stable model by default.
# You can still override this in .env with GEMINI_MODEL=...
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

# Automatic fallbacks if the primary model is temporarily overloaded.
FALLBACK_MODELS = [
    model
    for model in [
        PRIMARY_MODEL,
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]
    if model
]

# Remove duplicates while preserving order.
MODELS: List[str] = []
for model in FALLBACK_MODELS:
    if model not in MODELS:
        MODELS.append(model)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

PROMPT = """
You are the visual bathroom-analysis engine inside a Kohler bathroom design prototype.

Analyze ONLY what is visibly supported by the uploaded bathroom photograph.

Your job is not to generate an image. Your job is to understand the existing bathroom so the
customer can use the analysis as a starting point for a redesign.

IMPORTANT RULES:
- Do not estimate exact room dimensions from the photograph.
- Do not invent hidden plumbing, construction conditions, products, brands, measurements,
  materials, accessibility conditions, defects, or fixtures that are not visibly supported.
- If something cannot be identified confidently, say "Not confidently identified".
- Keep descriptions concise and useful for an interior-design workflow.
- Do not claim that a visible fixture is a Kohler product unless the image clearly establishes that.
- "Recommended categories" means product categories that could be considered during redesign,
  not claims about products currently installed.

Assess:
1. visible bathroom fixtures
2. current visual style
3. visible materials and finishes
4. lighting character
5. visible storage situation
6. practical/design opportunities visible from the image
7. one recommended design direction for the redesign
8. useful product categories for the next Kohler recommendation stage

For recommended_style, prefer one of these four design families when reasonable:
- Warm Minimal
- Bold Heritage
- Wellness
- Editorial Luxe

Return JSON only with exactly these keys:
{
  "detected_fixtures": ["string"],
  "current_style": "string",
  "materials": ["string"],
  "lighting": "string",
  "storage": "string",
  "improvements": ["string"],
  "recommended_style": "string",
  "recommended_categories": ["string"],
  "design_rationale": "string"
}

Keep detected_fixtures, materials, improvements, and recommended_categories compact.
Return 3 to 5 improvements at most.
"""


RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "detected_fixtures": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "current_style": {"type": "STRING"},
        "materials": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "lighting": {"type": "STRING"},
        "storage": {"type": "STRING"},
        "improvements": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "recommended_style": {"type": "STRING"},
        "recommended_categories": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "design_rationale": {"type": "STRING"},
    },
    "required": [
        "detected_fixtures",
        "current_style",
        "materials",
        "lighting",
        "storage",
        "improvements",
        "recommended_style",
        "recommended_categories",
        "design_rationale",
    ],
}


def _extract_text(payload: Dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []

    if not candidates:
        feedback = payload.get("promptFeedback") or {}
        reason = feedback.get("blockReason")

        if reason:
            raise RuntimeError(f"Gemini blocked the request: {reason}")

        raise RuntimeError("Gemini returned no analysis.")

    parts = candidates[0].get("content", {}).get("parts", [])

    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            return str(part["text"]).strip()

    raise RuntimeError("Gemini returned an empty analysis.")



def _parse_json_safely(text: str) -> Dict[str, Any]:
    """
    Gemini occasionally returns valid JSON wrapped in markdown fences or
    with a little text around it. Parse those cases instead of failing
    the whole bathroom-analysis request.
    """
    if not text:
        raise json.JSONDecodeError("Empty response", "", 0)

    cleaned = str(text).strip()

    # Remove ```json ... ``` / ``` ... ``` wrappers.
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    # Normal case.
    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Recover a JSON object if Gemini put prose before/after it.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")

    if first_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]

        parsed = json.loads(candidate)

        if isinstance(parsed, dict):
            return parsed

    # Raise a clean JSON error so the caller can retry/fallback.
    raise json.JSONDecodeError(
        "Could not parse Gemini bathroom analysis as JSON",
        cleaned,
        0,
    )

def _normalise(result: Dict[str, Any]) -> Dict[str, Any]:
    def clean_list(key, limit=8):
        value = result.get(key, [])

        if not isinstance(value, list):
            value = [value] if value else []

        cleaned = []

        for item in value:
            text = str(item).strip()

            if text and text not in cleaned:
                cleaned.append(text)

        return cleaned[:limit]

    return {
        "detected_fixtures": clean_list("detected_fixtures", 8),
        "current_style": str(
            result.get("current_style") or "Not confidently identified"
        ).strip(),
        "materials": clean_list("materials", 8),
        "lighting": str(
            result.get("lighting") or "Not confidently identified"
        ).strip(),
        "storage": str(
            result.get("storage") or "Not confidently identified"
        ).strip(),
        "improvements": clean_list("improvements", 5),
        "recommended_style": str(
            result.get("recommended_style") or "Warm Minimal"
        ).strip(),
        "recommended_categories": clean_list("recommended_categories", 8),
        "design_rationale": str(
            result.get("design_rationale") or ""
        ).strip(),
    }


def _call_model(
    model: str,
    image_base64: str,
    mime_type: str,
) -> Dict[str, Any]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_base64,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.0,
            "maxOutputTokens": 2000,
        },
    }

    response = requests.post(
        url,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )

    return {
        "status": response.status_code,
        "text": response.text,
        "json": response.json() if response.content else {},
    }


def analyze_bathroom_image(
    image_base64: str,
    mime_type: str,
) -> Dict[str, Any]:

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add GEMINI_API_KEY=your_key to backend/.env."
        )

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            "Only JPG, PNG and WEBP bathroom images are supported."
        )

    if not image_base64:
        raise ValueError("No bathroom image was supplied.")

    if len(image_base64) > 12_000_000:
        raise ValueError(
            "The bathroom image is too large. "
            "Use an image smaller than 8 MB."
        )

    # 503 = temporary model overload.
    # 429 = temporary rate/quota pressure.
    # 408/5xx = transient network/service issues.
    retryable_statuses = {
        408,
        429,
        500,
        502,
        503,
        504,
    }

    last_error = None

    for model_index, model in enumerate(MODELS):
        print(f"GEMINI ANALYZER MODEL: {model}")

        # A few short retries before switching to the next model.
        for attempt in range(3):
            result = _call_model(
                model=model,
                image_base64=image_base64,
                mime_type=mime_type,
            )

            status = result["status"]

            if status == 200:
                text = _extract_text(result["json"])

                try:
                    parsed = _parse_json_safely(text)

                    normalized = _normalise(parsed)

                    # Helpful for debugging; frontend does not depend on it.
                    normalized["_model_used"] = model

                    return normalized

                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    # A 200 response with malformed/truncated JSON should
                    # be retried just like a transient model failure.
                    last_error = (
                        f"{model} returned malformed JSON: {exc}. "
                        f"Raw response: {text[:500]}"
                    )

                    print(
                        f"GEMINI ATTEMPT {attempt + 1}/3 "
                        "RETURNED INVALID JSON"
                    )
                    print("RAW GEMINI TEXT:", text[:500])

                    if attempt < 2:
                        delay = (2 ** attempt) + random.uniform(0.15, 0.65)
                        print(
                            f"Retrying structured analysis in "
                            f"{delay:.1f}s..."
                        )
                        time.sleep(delay)

                    continue

            detail = str(result["text"])[:700]

            last_error = (
                f"{model} failed ({status}): {detail}"
            )

            print(
                f"GEMINI ATTEMPT {attempt + 1}/3 "
                f"FAILED: {status}"
            )

            if status not in retryable_statuses:
                # Invalid key, invalid request, unsupported model, etc.
                # No point hammering the same endpoint.
                break

            # Exponential backoff with jitter:
            # ~1s, ~2s, ~4s before moving on.
            if attempt < 2:
                delay = (2 ** attempt) + random.uniform(0.15, 0.65)
                print(
                    f"Transient Gemini error. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        # If one model is overloaded, immediately try the next fallback.
        if model_index < len(MODELS) - 1:
            print(
                f"Switching Gemini fallback: "
                f"{model} -> {MODELS[model_index + 1]}"
            )

    raise RuntimeError(
        "Gemini is temporarily unavailable after retries "
        "and fallback models. Please try again shortly. "
        f"Last error: {last_error}"
    )
