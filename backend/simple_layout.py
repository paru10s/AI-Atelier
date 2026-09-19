import re

FIXTURE_SIZES = {
    "basin": (3.0, 1.8),
    "toilet": (2.4, 3.0),
    "shower": (3.2, 3.2),
    "bathtub": (5.5, 2.8),
}

PLACEMENT_ORDER = [
    ("basin", "back_left"),
    ("shower", "back_right"),
    ("toilet", "front_right"),
    ("bathtub", "front_left"),
]


def extract_room_dimensions(room_text):
    """
    Pull width/depth in feet from strings such as:
    'Bathroom 12 ft width x 10 ft depth'
    """
    values = re.findall(r"(\d+(?:\.\d+)?)\s*ft", str(room_text), flags=re.I)

    if len(values) >= 2:
        return float(values[0]), float(values[1])

    # Safe fallback for the UI defaults.
    return 12.0, 10.0


def _fit_size(width, depth, room_width, room_depth):
    """
    Keep the viewer readable in smaller rooms without changing
    the actual room dimensions.
    """
    w = min(width, max(1.4, room_width * 0.42))
    d = min(depth, max(1.4, room_depth * 0.38))
    return round(w, 2), round(d, 2)


def _position(zone, fixture_width, fixture_depth, room_width, room_depth):
    margin = max(0.2, min(room_width, room_depth) * 0.035)

    if zone == "back_left":
        return margin, room_depth - fixture_depth - margin

    if zone == "back_right":
        return room_width - fixture_width - margin, room_depth - fixture_depth - margin

    if zone == "front_right":
        return room_width - fixture_width - margin, margin

    return margin, margin


def build_layout(room_text, selected_products):
    """
    Deterministic 3D-view layout only.

    IMPORTANT:
    This layout is NOT passed into Pollinations.
    Pollinations remains free to create the photorealistic image.
    """
    room_width, room_depth = extract_room_dimensions(room_text)

    selected_categories = {
        str(product.get("category", "")).lower()
        for product in selected_products
    }

    # Faucet belongs to the basin/wash station, so it is not a
    # separate 3D footprint.
    fixtures = {}

    for category, zone in PLACEMENT_ORDER:
        if category not in selected_categories:
            continue

        base_width, base_depth = FIXTURE_SIZES[category]
        fixture_width, fixture_depth = _fit_size(
            base_width,
            base_depth,
            room_width,
            room_depth,
        )

        x, y = _position(
            zone,
            fixture_width,
            fixture_depth,
            room_width,
            room_depth,
        )

        product = next(
            (
                item
                for item in selected_products
                if str(item.get("category", "")).lower() == category
            ),
            {},
        )

        fixtures[category] = {
            "x": round(max(0.0, x), 2),
            "y": round(max(0.0, y), 2),
            "width": fixture_width,
            "depth": fixture_depth,
            "product_name": product.get("name", category.title()),
            "price": product.get("price", 0),
        }

    return {
        "room": {
            "width": room_width,
            "depth": room_depth,
            "height": 9.0,
        },
        "fixtures": fixtures,
    }
