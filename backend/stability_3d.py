import os
import random
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "").strip()

BASE_DIR = Path(__file__).resolve().parent
GENERATED_MODELS_DIR = BASE_DIR / "generated_models"
GENERATED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

RETRYABLE_STATUS = {
    408,
    429,
    500,
    502,
    503,
    504,
}


def generate_3d_model_from_image(image_path: str) -> str:
    """
    Convert ONE generated bathroom visualization into a real GLB model
    using Stability AI's SPAR3D endpoint.

    This is not the old procedural bathroom sketch and not a flat image plane.
    The API returns an actual 3D .glb asset.
    """

    if not STABILITY_API_KEY:
        raise RuntimeError(
            "STABILITY_API_KEY is missing from backend/.env."
        )

    source = Path(image_path)

    if not source.exists():
        raise FileNotFoundError(
            f"Generated bathroom image not found: {source.name}"
        )

    if source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError(
            "3D generation requires a JPG, PNG or WEBP image."
        )

    url = (
        "https://api.stability.ai"
        "/v2beta/3d/stable-point-aware-3d"
    )

    last_error = None

    for attempt in range(3):
        try:
            with source.open("rb") as image_file:
                response = requests.post(
                    url,
                    headers={
                        "authorization": f"Bearer {STABILITY_API_KEY}",
                    },
                    files={
                        "image": (
                            source.name,
                            image_file,
                        )
                    },
                    data={
                        "texture_resolution": "1024",
                    },
                    timeout=240,
                )

            if response.status_code == 200:
                existing = list(
                    GENERATED_MODELS_DIR.glob("*.glb")
                )

                filename = (
                    f"bathroom_3d_{len(existing) + 1}.glb"
                )

                output_path = (
                    GENERATED_MODELS_DIR / filename
                )

                output_path.write_bytes(
                    response.content
                )

                print(
                    "STABILITY 3D MODEL SAVED:",
                    output_path
                )

                return str(output_path)

            last_error = (
                f"Stability 3D failed "
                f"({response.status_code}): "
                f"{response.text[:900]}"
            )

            print(
                f"STABILITY 3D ATTEMPT "
                f"{attempt + 1}/3 FAILED:",
                response.status_code,
            )

            if response.status_code not in RETRYABLE_STATUS:
                break

        except requests.RequestException as error:
            last_error = (
                f"Stability 3D request error: {error}"
            )

            print(
                f"STABILITY 3D ATTEMPT "
                f"{attempt + 1}/3 REQUEST ERROR:",
                error,
            )

        if attempt < 2:
            delay = (
                (2 ** attempt)
                + random.uniform(0.2, 0.8)
            )

            print(
                f"Retrying Stability 3D "
                f"in {delay:.1f}s..."
            )

            time.sleep(delay)

    raise RuntimeError(
        "Could not generate the 3D model. "
        f"Last error: {last_error}"
    )
