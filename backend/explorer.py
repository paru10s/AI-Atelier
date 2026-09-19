import itertools
import re

import products as product_catalog
from recommender import recommend_products


KOHLER_PRODUCTS = getattr(product_catalog, "KOHLER_PRODUCTS", [])


def _number(value, default=0):
    """Convert ₹ / comma formatted prices or numeric values to int."""
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return int(value)

    text = str(value)
    text = text.replace("₹", "").replace(",", "").strip()

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return default

    try:
        return int(float(match.group(0)))
    except (TypeError, ValueError):
        return default


def _category(product):
    return str(product.get("category", "")).strip().lower()


def _price(product):
    return max(0, _number(product.get("price", 0)))


def _product_signature(products):
    return tuple(
        (
            _category(product),
            str(
                product.get("sku")
                or product.get("id")
                or product.get("name")
                or ""
            ).strip().lower(),
        )
        for product in products
    )


def _product_search_text(product):
    """
    Use whatever descriptive fields already exist in products.py.
    No fabricated product metadata is introduced here.
    """
    fields = [
        product.get("name", ""),
        product.get("category", ""),
        product.get("style", ""),
        product.get("styles", ""),
        product.get("theme", ""),
        product.get("themes", ""),
        product.get("description", ""),
        product.get("finish", ""),
        product.get("collection", ""),
        product.get("tags", ""),
    ]

    pieces = []

    for field in fields:
        if isinstance(field, (list, tuple, set)):
            pieces.extend(str(x) for x in field)
        else:
            pieces.append(str(field))

    return " ".join(pieces).lower()


def _theme_words(style):
    words = re.findall(r"[a-z0-9]+", str(style).lower())

    stop_words = {
        "and", "the", "with", "for", "bathroom", "design",
        "style", "room", "a", "an", "of", "in", "to",
    }

    return [word for word in words if len(word) >= 3 and word not in stop_words]


def _style_score(products, style):
    """
    Small preference score used only as a tie-breaker between similarly
    priced real catalogue combinations.
    """
    words = _theme_words(style)

    if not words:
        return 0

    score = 0

    for product in products:
        text = _product_search_text(product)

        for word in words:
            if word in text:
                score += 1

    return score


def _catalogue_by_category(categories, baseline_products):
    """
    Build candidate lists from the user's actual products.py catalogue.
    If a category is missing from the catalogue for any reason, preserve
    the currently recommended product as a safe fallback.
    """
    result = {}

    for category in categories:
        candidates = [
            product
            for product in KOHLER_PRODUCTS
            if _category(product) == category and _price(product) > 0
        ]

        if not candidates:
            candidates = [
                product
                for product in baseline_products
                if _category(product) == category and _price(product) > 0
            ]

        # Remove exact duplicate SKUs/names while preserving real products.
        unique = []
        seen = set()

        for product in candidates:
            key = (
                str(
                    product.get("sku")
                    or product.get("id")
                    or product.get("name")
                    or ""
                ).strip().lower(),
                _price(product),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(product)

        # Sorting makes the final trade-off progression deterministic.
        result[category] = sorted(unique, key=_price)

    return result


def _build_combinations(candidate_map, categories):
    lists = [candidate_map.get(category, []) for category in categories]

    if not lists or any(not items for items in lists):
        return []

    combinations = []

    for combo in itertools.product(*lists):
        products = list(combo)
        cost = sum(_price(product) for product in products)

        combinations.append(
            {
                "products": products,
                "cost": cost,
                "signature": _product_signature(products),
            }
        )

    # Same set/cost should not appear multiple times.
    unique = {}
    for combo in combinations:
        unique[(combo["signature"], combo["cost"])] = combo

    return sorted(unique.values(), key=lambda item: item["cost"])


def _pick_from_band(
    feasible,
    style,
    percentile,
    used_signatures,
    previous_cost=None,
):
    """
    Pick a real combination from a price band.

    SMART     -> lower part of available catalogue
    BALANCED  -> middle
    ELEVATED  -> upper part

    Within a nearby price window, theme matching is used as a tie-breaker.
    """
    if not feasible:
        return None

    pool = [
        item
        for item in feasible
        if item["signature"] not in used_signatures
    ]

    if not pool:
        pool = feasible[:]

    # For later tiers prefer a genuinely higher final product total.
    if previous_cost is not None:
        higher = [item for item in pool if item["cost"] > previous_cost]

        if higher:
            pool = higher

    pool = sorted(pool, key=lambda item: item["cost"])

    if len(pool) == 1:
        chosen = pool[0]
        chosen["style_score"] = _style_score(chosen["products"], style)
        return chosen

    percentile = max(0.0, min(1.0, float(percentile)))
    target_index = int(round((len(pool) - 1) * percentile))

    # Search around the desired cost position, not across the whole list.
    # This prevents every tier from collapsing onto the same "best style" set.
    radius = max(2, int(len(pool) * 0.08))
    start = max(0, target_index - radius)
    end = min(len(pool), target_index + radius + 1)

    window = pool[start:end]

    target_cost = pool[target_index]["cost"]

    ranked = sorted(
        window,
        key=lambda item: (
            -_style_score(item["products"], style),
            abs(item["cost"] - target_cost),
            item["cost"],
        ),
    )

    chosen = ranked[0]
    chosen["style_score"] = _style_score(chosen["products"], style)

    return chosen


def _fallback_option(label, tier_budget, style, room):
    """
    Only used if products.py cannot produce combinations.
    Keeps the app working rather than failing the entire explorer.
    """
    result = recommend_products(
        str(tier_budget),
        style,
        room,
    )

    if not result.get("success"):
        return None

    products = result.get("products", [])
    total = _number(result.get("total", 0))

    return {
        "label": label,
        "budget": tier_budget,
        "cost": total,
        "remaining": max(0, tier_budget - total),
        "products": products,
        "style_score": _style_score(products, style),
    }


def build_budget_options(budget, style, room):
    """
    Build three genuinely different real-product trade-off levels.

    Important:
    - No image generation is called.
    - No fake products or fake prices are introduced.
    - Products always come from products.py / the existing recommender.
    - Tiers are chosen from different cost regions, so increasing the
      budget actually changes the product set and total whenever the
      catalogue contains alternatives.
    """

    base_budget = max(100000, _number(budget, 600000))

    tiers = [
        {
            "label": "SMART",
            "budget": max(100000, int(base_budget * 0.75)),
            "percentile": 0.18,
        },
        {
            "label": "BALANCED",
            "budget": base_budget,
            "percentile": 0.52,
        },
        {
            "label": "ELEVATED",
            "budget": int(base_budget * 1.25),
            "percentile": 0.86,
        },
    ]

    # Use the existing recommendation to determine which fixture categories
    # belong in this specific room. That keeps bathtub/no-bathtub behaviour
    # aligned with the main recommendation engine.
    baseline = recommend_products(
        str(base_budget),
        style,
        room,
    )

    baseline_products = (
        baseline.get("products", [])
        if baseline.get("success")
        else []
    )

    categories = []

    for product in baseline_products:
        category = _category(product)

        if category and category not in categories:
            categories.append(category)

    # Safe fallback if the current recommender returns no product list.
    if not categories:
        categories = ["basin", "faucet", "toilet", "shower"]

    candidate_map = _catalogue_by_category(
        categories,
        baseline_products,
    )

    combinations = _build_combinations(
        candidate_map,
        categories,
    )

    # If the catalogue cannot be combined, retain the previous
    # recommender-based behaviour instead of crashing.
    if not combinations:
        fallback = []

        for tier in tiers:
            option = _fallback_option(
                tier["label"],
                tier["budget"],
                style,
                room,
            )

            if option:
                fallback.append(option)

        return fallback

    options = []
    used_signatures = set()
    previous_cost = None

    for tier in tiers:
        feasible = [
            combo
            for combo in combinations
            if combo["cost"] <= tier["budget"]
        ]

        # If this budget is below the cheapest complete set, let the existing
        # recommender decide how to handle it.
        if not feasible:
            option = _fallback_option(
                tier["label"],
                tier["budget"],
                style,
                room,
            )

            if option:
                signature = _product_signature(option["products"])

                # Don't intentionally repeat a previous fallback.
                if signature not in used_signatures:
                    used_signatures.add(signature)

                options.append(option)
                previous_cost = option["cost"]

            continue

        chosen = _pick_from_band(
            feasible=feasible,
            style=style,
            percentile=tier["percentile"],
            used_signatures=used_signatures,
            previous_cost=previous_cost,
        )

        if not chosen:
            continue

        used_signatures.add(chosen["signature"])
        previous_cost = chosen["cost"]

        options.append(
            {
                "label": tier["label"],
                "budget": tier["budget"],
                "cost": chosen["cost"],
                "remaining": max(
                    0,
                    tier["budget"] - chosen["cost"],
                ),
                "products": chosen["products"],
                "style_score": chosen.get("style_score", 0),
            }
        )

    return options
