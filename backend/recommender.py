from products import KOHLER_PRODUCTS
import re


# =====================================================
# PRODUCT CATEGORIES
# =====================================================

CORE_CATEGORIES = [
    "basin",
    "faucet",
    "toilet",
    "shower"
]

OPTIONAL_CATEGORIES = [
    "bathtub"
]


# =====================================================
# THEME PROCESSING
# =====================================================

def get_theme_words(theme):

    return set(
        theme.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("-", " ")
        .split()
    )


def calculate_style_score(product, theme_words):

    product_styles = {
        style.lower()
        for style in product.get("styles", [])
    }

    matches = product_styles.intersection(theme_words)

    return len(matches)


# =====================================================
# ROOM DIMENSION EXTRACTION
# =====================================================

def extract_room_dimensions(room):

    """
    Example input:

    Bathroom - 10 ft wide x 8 ft deep

    Returns:

    width = 10
    depth = 8
    area = 80
    """

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        room
    )

    if len(numbers) < 2:
        return None, None, None

    width = float(numbers[0])
    depth = float(numbers[1])

    area = width * depth

    return width, depth, area


# =====================================================
# CHEAPEST PRODUCT
# =====================================================

def get_minimum_category_cost(category):

    products = [
        product
        for product in KOHLER_PRODUCTS
        if product["category"] == category
    ]

    if not products:
        return 0

    return min(
        product["price"]
        for product in products
    )


# =====================================================
# MAIN RECOMMENDATION ENGINE
# =====================================================

def recommend_products(budget, theme, room):

    try:

        budget = float(budget)

    except (ValueError, TypeError):

        return {
            "success": False,
            "message": "Invalid budget.",
            "products": [],
            "total": 0
        }


    if budget <= 0:

        return {
            "success": False,
            "message": "Budget must be greater than zero.",
            "products": [],
            "total": 0
        }


    theme_words = get_theme_words(theme)

    width, depth, area = extract_room_dimensions(room)


    print("\nROOM ANALYSIS:")
    print("Width:", width)
    print("Depth:", depth)
    print("Area:", area)


    selected_products = []

    remaining_budget = budget


    # =====================================================
    # STEP 1
    # SELECT CORE PRODUCTS
    # =====================================================

    for category_index, category in enumerate(
        CORE_CATEGORIES
    ):

        category_products = [

            product

            for product in KOHLER_PRODUCTS

            if product["category"] == category

        ]


        if not category_products:

            return {
                "success": False,
                "message":
                    f"No products available for {category}.",
                "products": [],
                "total": 0
            }


        # Sort by:
        # 1. theme compatibility
        # 2. cheaper product

        category_products.sort(

            key=lambda product: (

                -calculate_style_score(
                    product,
                    theme_words
                ),

                product["price"]

            )

        )


        # Reserve minimum money required
        # for remaining core categories

        future_categories = (
            CORE_CATEGORIES[
                category_index + 1:
            ]
        )


        minimum_future_cost = sum(

            get_minimum_category_cost(
                future_category
            )

            for future_category
            in future_categories

        )


        affordable_products = [

            product

            for product in category_products

            if (
                product["price"]
                + minimum_future_cost
                <= remaining_budget
            )

        ]


        if not affordable_products:

            return {

                "success": False,

                "message": (
                    "Budget is too low to select "
                    "the required Kohler bathroom products."
                ),

                "products": [],

                "total": 0
            }


        chosen = affordable_products[0]

        selected_products.append(chosen)

        remaining_budget -= chosen["price"]


    # =====================================================
    # STEP 2
    # CHECK WHETHER BATHTUB MAKES SENSE
    # =====================================================

    bathtub_added = False


    bathtub_products = [

        product

        for product in KOHLER_PRODUCTS

        if product["category"] == "bathtub"

    ]


    if bathtub_products and area is not None:

        cheapest_bathtub = min(
            product["price"]
            for product in bathtub_products
        )


        # -------------------------------------------------
        # BATHTUB RULES
        # -------------------------------------------------
        #
        # For this prototype:
        #
        # Minimum room area = 70 sq ft
        #
        # Minimum room side = 7 ft
        #
        # Bathtub must fit inside remaining
        # product budget.
        #
        # -------------------------------------------------

        room_large_enough = (
            area >= 70
            and width >= 7
            and depth >= 7
        )


        budget_allows_bathtub = (
            remaining_budget >= cheapest_bathtub
        )


        print("\nBATHTUB ANALYSIS:")

        print(
            "Room large enough:",
            room_large_enough
        )

        print(
            "Remaining budget:",
            remaining_budget
        )

        print(
            "Cheapest bathtub:",
            cheapest_bathtub
        )


        if (
            room_large_enough
            and budget_allows_bathtub
        ):

            affordable_bathtubs = [

                product

                for product in bathtub_products

                if product["price"]
                <= remaining_budget

            ]


            affordable_bathtubs.sort(

                key=lambda product: (

                    -calculate_style_score(
                        product,
                        theme_words
                    ),

                    -product["price"]

                )

            )


            chosen_bathtub = (
                affordable_bathtubs[0]
            )


            selected_products.append(
                chosen_bathtub
            )


            remaining_budget -= (
                chosen_bathtub["price"]
            )


            bathtub_added = True


    # =====================================================
    # STEP 3
    # UPGRADE CORE PRODUCTS USING REMAINING MONEY
    # =====================================================

    for index, selected in enumerate(
        selected_products
    ):

        # Don't replace bathtub here
        if selected["category"] == "bathtub":
            continue


        category = selected["category"]


        alternatives = [

            product

            for product in KOHLER_PRODUCTS

            if (
                product["category"] == category
                and product["price"]
                > selected["price"]
            )

        ]


        alternatives.sort(

            key=lambda product: (

                -calculate_style_score(
                    product,
                    theme_words
                ),

                -product["price"]

            )

        )


        for alternative in alternatives:

            upgrade_cost = (
                alternative["price"]
                - selected["price"]
            )


            if upgrade_cost <= remaining_budget:

                selected_products[index] = (
                    alternative
                )

                remaining_budget -= (
                    upgrade_cost
                )

                break


    # =====================================================
    # TOTAL
    # =====================================================

    total = sum(

        product["price"]

        for product in selected_products

    )


    return {

        "success": True,

        "message":
            "Kohler products selected successfully.",

        "products":
            selected_products,

        "total":
            total,

        "remaining_budget":
            budget - total,

        "room_area_sqft":
            area,

        "bathtub_added":
            bathtub_added

    }