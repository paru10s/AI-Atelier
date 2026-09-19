import base64
import os
import random
import time
from pathlib import Path
from typing import Iterable, List

import requests
from dotenv import load_dotenv

load_dotenv()

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "").strip()

BASE_DIR = Path(__file__).resolve().parent
GENERATED_FOLDER = BASE_DIR / "generated_designs"
GENERATED_FOLDER.mkdir(parents=True, exist_ok=True)

STRUCTURE_CREDIT_COST = 5.0
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _clean_items(values: Iterable[str]) -> List[str]:
    result = []

    for value in values or []:
        text = str(value).strip()

        if text:
            result.append(text)

    return result


def _get_stability_balance() -> float:
    if not STABILITY_API_KEY:
        raise RuntimeError(
            "STABILITY_API_KEY is missing from backend/.env."
        )

    try:
        response = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not verify Stability credit balance. "
            "No paid generation was started."
        ) from exc

    if response.status_code == 401:
        raise RuntimeError(
            "The Stability API key is invalid. "
            "No paid generation was started."
        )

    if response.status_code != 200:
        raise RuntimeError(
            "Could not verify Stability credit balance. "
            "No paid generation was started. "
            f"Status: {response.status_code}"
        )

    try:
        credits = float(response.json().get("credits", 0))
    except (TypeError, ValueError, AttributeError) as exc:
        raise RuntimeError(
            "Stability returned an unreadable credit balance. "
            "No paid generation was started."
        ) from exc

    return credits


def _require_credits(required: float) -> float:
    balance = _get_stability_balance()

    if balance < required:
        raise RuntimeError(
            f"Not enough Stability credits. "
            f"This redesign requires {required:g} credits, "
            f"but the account currently has {balance:.2f}. "
            "No paid generation was started."
        )

    return balance


def _build_prompt(
    recommended_style: str = "",
    design_rationale: str = "",
    improvements=None,
):
    style = (
        str(recommended_style or "").strip()
        or "warm minimal luxury"
    )

    rationale = str(
        design_rationale or ""
    ).strip()

    improvement_items = _clean_items(
        improvements or []
    )

    improvement_lines = "\n".join(
        f"- {item}"
        for item in improvement_items
    )

    if not improvement_lines:
        improvement_lines = (
            "- improve storage\n"
            "- improve lighting\n"
            "- improve material coherence"
        )

    return f"""
Redesign this SAME uploaded bathroom photograph into one photorealistic finished premium bathroom.

Preserve the same room structure, visible walls, openings, camera viewpoint and overall proportions.
Keep it recognizably the same bathroom, but redesign it professionally.

Recommended design direction:
{style}

Design rationale:
{rationale}

Improvement priorities:
{improvement_lines}

Use a Kohler-inspired premium bathroom look with better finishes, better lighting, refined fixtures,
cleaner detailing, elegant vanity design and a more cohesive interior.

Important:
- preserve the existing architectural layout and viewpoint
- keep only one sink / vanity zone unless the original photo clearly has more
- keep only one toilet unless the original photo clearly has more
- keep only one shower zone unless the original photo clearly has more
- do not create duplicate sanitary fixtures
- do not create impossible plumbing
- do not turn it into a floor plan, collage, drawing or rendering board
- no text, no labels, no pricing, no annotations
- no people
- the result must be a realistic premium interior photograph
""".strip()


def _decode_image(image_base64: str) -> bytes:
    try:
        return base64.b64decode(
            image_base64,
            validate=True,
        )
    except Exception as exc:
        raise ValueError(
            "Invalid uploaded bathroom photo."
        ) from exc


def _save_image(
    image_bytes: bytes,
    extension: str = ".jpg",
) -> str:
    timestamp = int(time.time() * 1000)

    filename = (
        f"stability_redesign_{timestamp}{extension}"
    )

    filepath = GENERATED_FOLDER / filename
    filepath.write_bytes(image_bytes)

    return str(filepath)


def generate_photo_redesign(
    image_base64,
    mime_type,
    recommended_style="",
    design_rationale="",
    improvements=None,
):
    if not STABILITY_API_KEY:
        raise RuntimeError(
            "STABILITY_API_KEY is missing from backend/.env."
        )

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            "Only JPG, PNG and WEBP bathroom photos are supported."
        )

    if not image_base64:
        raise ValueError(
            "No bathroom photo was supplied."
        )

    image_bytes = _decode_image(
        image_base64
    )

    if len(image_bytes) > 10 * 1024 * 1024:
        raise ValueError(
            "The prepared bathroom image exceeds Stability's "
            "10 MiB request limit. No paid generation was started."
        )

    prompt = _build_prompt(
        recommended_style=recommended_style,
        design_rationale=design_rationale,
        improvements=improvements or [],
    )

    # FREE preflight check. If the key/balance is wrong,
    # stop before the 5-credit endpoint is called.
    balance = _require_credits(
        STRUCTURE_CREDIT_COST
    )

    print(
        f"STABILITY BALANCE BEFORE REDESIGN: "
        f"{balance:.2f} credits"
    )

    url = (
        "https://api.stability.ai"
        "/v2beta/stable-image/control/structure"
    )

    negative_prompt = (
        "duplicate sink, duplicate vanity, duplicate toilet, "
        "duplicate bathtub, duplicate shower, extra sanitary fixtures, "
        "collage, floor plan, sketch, diagram, text, labels, watermark, "
        "distorted geometry, unrealistic plumbing, people"
    )

    last_error = None

    for attempt in range(3):
        try:
            response = requests.post(
                url,
                headers={
                    "authorization": (
                        f"Bearer {STABILITY_API_KEY}"
                    ),
                    "accept": "image/*",
                },
                files={
                    "image": (
                        f"bathroom"
                        f"{ALLOWED_MIME_TYPES[mime_type]}",
                        image_bytes,
                        mime_type,
                    )
                },
                data={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "control_strength": "0.78",
                    "output_format": "jpeg",
                },
                timeout=240,
            )

            if response.status_code == 200:
                filepath = _save_image(
                    response.content,
                    ".jpg",
                )

                print(
                    "STABILITY REDESIGN SAVED:",
                    filepath,
                )

                return filepath

            last_error = (
                f"Stability failed "
                f"({response.status_code}): "
                f"{response.text[:900]}"
            )

            print(
                f"STABILITY ATTEMPT "
                f"{attempt + 1}/3 FAILED:",
                response.status_code,
            )

            if response.status_code not in RETRYABLE_STATUS:
                break

        except requests.RequestException as exc:
            last_error = (
                f"Stability request error: {exc}"
            )

            print(
                f"STABILITY ATTEMPT "
                f"{attempt + 1}/3 REQUEST ERROR:",
                exc,
            )

        if attempt < 2:
            delay = (
                (2 ** attempt)
                + random.uniform(0.2, 0.8)
            )

            print(
                f"Retrying Stability in "
                f"{delay:.1f}s..."
            )

            time.sleep(delay)

    raise RuntimeError(
        "Stability bathroom redesign failed. "
        "Stability documents failed generations as uncharged. "
        f"Last error: {last_error}"
    )
