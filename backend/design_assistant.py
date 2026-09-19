import re


def _number(value, default=600000):
    try:
        return int(float(str(value).replace(",", "").replace("₹", "").strip()))
    except (TypeError, ValueError):
        return default


def _extract_budget(message):
    text = message.lower().replace(",", "")

    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)", text)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 100000)

    rupee_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d{5,8})", text)
    if rupee_match:
        return int(rupee_match.group(1))

    return None


def suggest_edit(message, budget, style):
    """
    Converts a short natural-language request into safe design settings.
    It does NOT call Pollinations and therefore costs no image-generation credit.
    """
    original_budget = _number(budget)
    new_budget = original_budget
    new_style = str(style or "").strip()
    text = str(message or "").strip()
    lower = text.lower()

    changes = []

    explicit_budget = _extract_budget(lower)

    if explicit_budget is not None:
        new_budget = max(100000, explicit_budget)
        changes.append(f"budget set to ₹{new_budget:,}")

    elif any(word in lower for word in ["cheaper", "lower budget", "reduce budget", "less expensive", "save money"]):
        new_budget = max(100000, int(original_budget * 0.85))
        changes.append("budget reduced by about 15%")

    elif any(word in lower for word in ["increase budget", "more budget", "spend more"]):
        new_budget = int(original_budget * 1.15)
        changes.append("budget increased by about 15%")

    style_additions = []

    if any(word in lower for word in ["warmer", "warm", "cozy"]):
        style_additions.append("warm layered lighting, natural wood tones, soft neutral stone")

    if any(word in lower for word in ["luxury", "luxurious", "premium", "more elegant"]):
        style_additions.append("more luxurious premium detailing, refined stone and metal finishes")

    if any(word in lower for word in ["minimal", "minimalist", "cleaner"]):
        style_additions.append("minimalist, uncluttered, calm, clean-lined")

    if any(word in lower for word in ["brighter", "bright", "airy"]):
        style_additions.append("bright natural daylight, airy palette, soft reflective surfaces")

    if any(word in lower for word in ["dark", "moody", "dramatic"]):
        style_additions.append("moody architectural lighting, deeper tones, dramatic contrast")

    if any(word in lower for word in ["zen", "spa", "wellness"]):
        style_additions.append("spa-like wellness atmosphere, tactile natural materials, serene lighting")

    if style_additions:
        addition = ", ".join(style_additions)
        new_style = f"{new_style}, {addition}".strip(", ")
        changes.append("aesthetic updated")

    if not changes:
        return {
            "success": True,
            "budget": original_budget,
            "style": new_style,
            "changed": False,
            "message": (
                "I can prepare changes such as: make it warmer, more luxurious, "
                "more minimal, brighter, moodier, cheaper, or set a new budget."
            ),
        }

    return {
        "success": True,
        "budget": new_budget,
        "style": new_style,
        "changed": True,
        "message": "Prepared: " + "; ".join(changes) + ". Review it before regenerating.",
    }
