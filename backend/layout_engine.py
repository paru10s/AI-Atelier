import re
import itertools


# =====================================================
# CONSTANTS
# =====================================================

CM_TO_FT = 0.0328084
WALL_MARGIN = 0.25

DEFAULT_FIXTURE_SIZES = {
    "basin": {
        "width": 2.0,
        "depth": 1.5
    },

    "toilet": {
        "width": 2.0,
        "depth": 2.3
    },

    "shower": {
        "width": 3.0,
        "depth": 3.0
    }
}


# =====================================================
# EXTRACT ROOM DIMENSIONS
# =====================================================

def extract_dimensions(room):

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        room
    )

    if len(numbers) < 2:
        return None, None

    return (
        float(numbers[0]),
        float(numbers[1])
    )


# =====================================================
# FIND PRODUCT
# =====================================================

def find_product(selected_products, category):

    for product in selected_products:

        if product.get("category") == category:
            return product

    return None


# =====================================================
# BATHTUB DIMENSIONS
# =====================================================

def get_bathtub_size(product):

    if not product:

        return None

    length_cm = product.get("length_cm")
    width_cm = product.get("width_cm")

    if not length_cm or not width_cm:

        return {
            "width": 5.5,
            "depth": 2.5
        }

    return {
        "width": round(
            length_cm * CM_TO_FT,
            2
        ),

        "depth": round(
            width_cm * CM_TO_FT,
            2
        )
    }


# =====================================================
# RECTANGLE COLLISION
# =====================================================

def rectangles_overlap(a, b):

    return not (

        a["x"] + a["width"] <= b["x"]

        or

        b["x"] + b["width"] <= a["x"]

        or

        a["y"] + a["depth"] <= b["y"]

        or

        b["y"] + b["depth"] <= a["y"]

    )


# =====================================================
# ROOM BOUNDARY CHECK
# =====================================================

def inside_room(
    fixture,
    room_width,
    room_depth
):

    return (

        fixture["x"] >= 0

        and

        fixture["y"] >= 0

        and

        fixture["x"] + fixture["width"]
        <= room_width

        and

        fixture["y"] + fixture["depth"]
        <= room_depth

    )


# =====================================================
# CREATE FIXTURE
# =====================================================

def create_fixture(
    x,
    y,
    width,
    depth,
    wall,
    product
):

    return {

        "x": round(x, 2),

        "y": round(y, 2),

        "width": round(width, 2),

        "depth": round(depth, 2),

        "wall": wall,

        "product": product
    }


# =====================================================
# BASIN CANDIDATE POSITIONS
# =====================================================

def basin_candidates(
    room_width,
    room_depth,
    product
):

    size = DEFAULT_FIXTURE_SIZES["basin"]

    w = size["width"]
    d = size["depth"]

    candidates = []


    # Front-left
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            WALL_MARGIN,
            w,
            d,
            "front-left",
            product["name"]
        )

    )


    # Front-right
    candidates.append(

        create_fixture(
            room_width - w - WALL_MARGIN,
            WALL_MARGIN,
            w,
            d,
            "front-right",
            product["name"]
        )

    )


    # Left-middle
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            room_depth / 2 - d / 2,
            w,
            d,
            "left",
            product["name"]
        )

    )


    # Right-middle
    candidates.append(

        create_fixture(
            room_width - w - WALL_MARGIN,
            room_depth / 2 - d / 2,
            w,
            d,
            "right",
            product["name"]
        )

    )


    return candidates


# =====================================================
# TOILET CANDIDATE POSITIONS
# =====================================================

def toilet_candidates(
    room_width,
    room_depth,
    product
):

    size = DEFAULT_FIXTURE_SIZES["toilet"]

    w = size["width"]
    d = size["depth"]

    candidates = []


    # Right-middle
    candidates.append(

        create_fixture(
            room_width - w - WALL_MARGIN,
            room_depth / 2 - d / 2,
            w,
            d,
            "right",
            product["name"]
        )

    )


    # Left-middle
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            room_depth / 2 - d / 2,
            w,
            d,
            "left",
            product["name"]
        )

    )


    # Front-right
    candidates.append(

        create_fixture(
            room_width - w - WALL_MARGIN,
            WALL_MARGIN,
            w,
            d,
            "front-right",
            product["name"]
        )

    )


    # Front-left
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            WALL_MARGIN,
            w,
            d,
            "front-left",
            product["name"]
        )

    )


    return candidates


# =====================================================
# SHOWER CANDIDATE POSITIONS
# =====================================================

def shower_candidates(
    room_width,
    room_depth,
    product
):

    size = DEFAULT_FIXTURE_SIZES["shower"]

    w = size["width"]
    d = size["depth"]

    candidates = []


    # Back-left
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            room_depth - d - WALL_MARGIN,
            w,
            d,
            "back-left",
            product["name"]
        )

    )


    # Back-right
    candidates.append(

        create_fixture(
            room_width - w - WALL_MARGIN,
            room_depth - d - WALL_MARGIN,
            w,
            d,
            "back-right",
            product["name"]
        )

    )


    return candidates


# =====================================================
# BATHTUB CANDIDATE POSITIONS
# =====================================================

def bathtub_candidates(
    room_width,
    room_depth,
    product
):

    size = get_bathtub_size(product)

    length = size["width"]
    short_side = size["depth"]

    candidates = []


    # -------------------------------------------------
    # HORIZONTAL ORIENTATION
    # -------------------------------------------------

    horizontal_w = length
    horizontal_d = short_side


    # Back-left
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            room_depth
            - horizontal_d
            - WALL_MARGIN,
            horizontal_w,
            horizontal_d,
            "back-left",
            product["name"]
        )

    )


    # Back-right
    candidates.append(

        create_fixture(
            room_width
            - horizontal_w
            - WALL_MARGIN,
            room_depth
            - horizontal_d
            - WALL_MARGIN,
            horizontal_w,
            horizontal_d,
            "back-right",
            product["name"]
        )

    )


    # -------------------------------------------------
    # VERTICAL ORIENTATION
    # Rotate bathtub 90 degrees
    # -------------------------------------------------

    vertical_w = short_side
    vertical_d = length


    # Left-back
    candidates.append(

        create_fixture(
            WALL_MARGIN,
            room_depth
            - vertical_d
            - WALL_MARGIN,
            vertical_w,
            vertical_d,
            "left",
            product["name"]
        )

    )


    # Right-back
    candidates.append(

        create_fixture(
            room_width
            - vertical_w
            - WALL_MARGIN,
            room_depth
            - vertical_d
            - WALL_MARGIN,
            vertical_w,
            vertical_d,
            "right",
            product["name"]
        )

    )


    return candidates


# =====================================================
# TOILET CLEARANCE
# =====================================================

def create_toilet_clearance(toilet):

    clearance_depth = 2.0


    # Our current toilet rectangles extend
    # from front toward the back of the room.
    # Therefore clear floor space is placed
    # immediately in front of the toilet.

    clearance_y = (
        toilet["y"]
        - clearance_depth
    )


    return {

        "x": toilet["x"],

        "y": round(clearance_y, 2),

        "width": toilet["width"],

        "depth": clearance_depth
    }


# =====================================================
# VALIDATE CANDIDATE LAYOUT
# =====================================================

def validate_layout(
    fixtures,
    room_width,
    room_depth
):

    errors = []


    # -------------------------------------------------
    # ROOM BOUNDARIES
    # -------------------------------------------------

    for name, fixture in fixtures.items():

        if not inside_room(
            fixture,
            room_width,
            room_depth
        ):

            errors.append(
                f"{name} outside room boundary"
            )


    # -------------------------------------------------
    # FIXTURE COLLISIONS
    # -------------------------------------------------

    names = list(fixtures.keys())


    for i in range(len(names)):

        for j in range(i + 1, len(names)):

            name_a = names[i]
            name_b = names[j]

            if rectangles_overlap(
                fixtures[name_a],
                fixtures[name_b]
            ):

                errors.append(
                    f"{name_a} overlaps {name_b}"
                )


    # -------------------------------------------------
    # TOILET CLEARANCE
    # -------------------------------------------------

    toilet_clearance = None


    if "toilet" in fixtures:

        toilet_clearance = (
            create_toilet_clearance(
                fixtures["toilet"]
            )
        )


        if not inside_room(
            toilet_clearance,
            room_width,
            room_depth
        ):

            errors.append(
                "toilet front clearance outside room"
            )


        else:

            for name, fixture in fixtures.items():

                if name == "toilet":
                    continue


                if rectangles_overlap(
                    toilet_clearance,
                    fixture
                ):

                    errors.append(
                        f"{name} blocks toilet clearance"
                    )


    return (
        len(errors) == 0,
        errors,
        toilet_clearance
    )


# =====================================================
# LAYOUT SCORE
# =====================================================

def calculate_layout_score(
    fixtures,
    room_width,
    room_depth
):

    """
    Higher score = preferred layout.

    This does NOT decide whether a layout is valid.
    Validation happens separately.

    It only helps us choose between several valid
    arrangements.
    """

    score = 0


    # -------------------------------------------------
    # Prefer shower toward rear
    # -------------------------------------------------

    if "shower" in fixtures:

        if "back" in fixtures["shower"]["wall"]:

            score += 20


    # -------------------------------------------------
    # Prefer bathtub toward rear
    # -------------------------------------------------

    if "bathtub" in fixtures:

        bathtub = fixtures["bathtub"]

        if (
            "back" in bathtub["wall"]
            or bathtub["y"] > room_depth / 2
        ):

            score += 20


    # -------------------------------------------------
    # Prefer basin toward front
    # -------------------------------------------------

    if "basin" in fixtures:

        basin = fixtures["basin"]

        if basin["y"] < room_depth / 2:

            score += 15


    # -------------------------------------------------
    # Prefer toilet away from entrance/front
    # -------------------------------------------------

    if "toilet" in fixtures:

        toilet = fixtures["toilet"]

        if toilet["y"] > 1.5:

            score += 15


    # -------------------------------------------------
    # Reward distance between toilet and bathtub
    # -------------------------------------------------

    if (
        "toilet" in fixtures
        and
        "bathtub" in fixtures
    ):

        toilet = fixtures["toilet"]
        bathtub = fixtures["bathtub"]

        toilet_center_x = (
            toilet["x"]
            + toilet["width"] / 2
        )

        toilet_center_y = (
            toilet["y"]
            + toilet["depth"] / 2
        )

        bathtub_center_x = (
            bathtub["x"]
            + bathtub["width"] / 2
        )

        bathtub_center_y = (
            bathtub["y"]
            + bathtub["depth"] / 2
        )

        distance = (

            (
                toilet_center_x
                - bathtub_center_x
            ) ** 2

            +

            (
                toilet_center_y
                - bathtub_center_y
            ) ** 2

        ) ** 0.5


        score += min(
            distance * 3,
            20
        )


    return round(score, 2)


# =====================================================
# MAIN AUTOMATIC LAYOUT SEARCH
# =====================================================

def generate_layout(
    room,
    selected_products
):

    room_width, room_depth = (
        extract_dimensions(room)
    )


    if room_width is None or room_depth is None:

        return {

            "success": False,

            "layout_valid": False,

            "message":
                "Could not determine room dimensions.",

            "errors": [
                "Invalid room dimensions"
            ]
        }


    area = (
        room_width
        * room_depth
    )


    # =================================================
    # PRODUCTS
    # =================================================

    basin_product = find_product(
        selected_products,
        "basin"
    )

    toilet_product = find_product(
        selected_products,
        "toilet"
    )

    shower_product = find_product(
        selected_products,
        "shower"
    )

    bathtub_product = find_product(
        selected_products,
        "bathtub"
    )


    # =================================================
    # CREATE CANDIDATE LISTS
    # =================================================

    candidate_groups = []
    fixture_names = []


    if basin_product:

        fixture_names.append("basin")

        candidate_groups.append(

            basin_candidates(
                room_width,
                room_depth,
                basin_product
            )

        )


    if toilet_product:

        fixture_names.append("toilet")

        candidate_groups.append(

            toilet_candidates(
                room_width,
                room_depth,
                toilet_product
            )

        )


    if shower_product:

        fixture_names.append("shower")

        candidate_groups.append(

            shower_candidates(
                room_width,
                room_depth,
                shower_product
            )

        )


    if bathtub_product:

        fixture_names.append("bathtub")

        candidate_groups.append(

            bathtub_candidates(
                room_width,
                room_depth,
                bathtub_product
            )

        )


    # =================================================
    # SEARCH ALL COMBINATIONS
    # =================================================

    valid_layouts = []

    tested_layouts = 0


    for combination in itertools.product(
        *candidate_groups
    ):

        tested_layouts += 1


        fixtures = {

            fixture_names[index]:
                combination[index]

            for index in range(
                len(fixture_names)
            )

        }


        (
            valid,
            errors,
            toilet_clearance

        ) = validate_layout(

            fixtures,
            room_width,
            room_depth
        )


        if valid:

            score = calculate_layout_score(
                fixtures,
                room_width,
                room_depth
            )


            valid_layouts.append({

                "fixtures":
                    fixtures,

                "toilet_clearance":
                    toilet_clearance,

                "score":
                    score

            })


    # =================================================
    # NO VALID LAYOUT FOUND
    # =================================================

    if not valid_layouts:

        return {

            "success": True,

            "layout_valid": False,

            "room": {

                "width_ft":
                    room_width,

                "depth_ft":
                    room_depth,

                "area_sqft":
                    round(area, 2)

            },

            "fixtures": {},

            "toilet_clearance":
                None,

            "layouts_tested":
                tested_layouts,

            "valid_layouts_found":
                0,

            "score":
                0,

            "errors": [

                (
                    "No collision-free layout "
                    "could be found for the "
                    "selected fixtures in this "
                    "room."
                )

            ]

        }


    # =================================================
    # CHOOSE BEST VALID LAYOUT
    # =================================================

    valid_layouts.sort(

        key=lambda layout:
            layout["score"],

        reverse=True

    )


    best = valid_layouts[0]


    return {

        "success": True,

        "layout_valid": True,

        "room": {

            "width_ft":
                room_width,

            "depth_ft":
                room_depth,

            "area_sqft":
                round(area, 2)

        },

        "fixtures":
            best["fixtures"],

        "toilet_clearance":
            best["toilet_clearance"],

        "layouts_tested":
            tested_layouts,

        "valid_layouts_found":
            len(valid_layouts),

        "score":
            best["score"],

        "errors": []

    }


# =====================================================
# CONVERT LAYOUT TO TEXT
# =====================================================

def layout_to_prompt(layout):

    if not layout.get("success"):

        return ""


    if not layout.get("layout_valid"):

        return (
            "No valid architectural layout "
            "was found."
        )


    room = layout["room"]


    lines = [

        "ARCHITECTURAL FLOOR PLAN:",

        "",

        (
            f"Room dimensions: "
            f"{room['width_ft']} ft wide x "
            f"{room['depth_ft']} ft deep."
        ),

        (
            f"Floor area: "
            f"{room['area_sqft']} square feet."
        ),

        "",

        (
            "Coordinate system: "
            "(0,0) represents the "
            "front-left corner."
        ),

        "",

        "FIXTURE PLACEMENT:"
    ]


    for name, fixture in (
        layout["fixtures"].items()
    ):

        lines.append(

            (
                f"- {name.upper()}: "
                f"x={fixture['x']} ft, "
                f"y={fixture['y']} ft, "
                f"width={fixture['width']} ft, "
                f"depth={fixture['depth']} ft. "
                f"Placement zone: "
                f"{fixture['wall']}."
            )

        )


    if layout.get("toilet_clearance"):

        clearance = (
            layout["toilet_clearance"]
        )


        lines.extend([

            "",

            (
                "TOILET CLEARANCE ZONE: "
                f"x={clearance['x']} ft, "
                f"y={clearance['y']} ft, "
                f"width={clearance['width']} ft, "
                f"depth={clearance['depth']} ft."
            )

        ])


    lines.extend([

        "",

        (
            "The selected layout has been "
            "validated for room boundaries, "
            "fixture collisions and toilet "
            "front clearance."
        )

    ])


    return "\n".join(lines)


# =====================================================
# PRINT LAYOUT
# =====================================================

def print_layout(layout):

    print("\n====================================")

    print("AUTOMATIC BATHROOM LAYOUT")

    print("====================================")


    if not layout.get("success"):

        print(
            layout.get(
                "message",
                "Layout generation failed."
            )
        )

        return


    room = layout.get("room", {})


    print(

        f"Room: "
        f"{room.get('width_ft')} ft × "
        f"{room.get('depth_ft')} ft"

    )


    print(

        f"Area: "
        f"{room.get('area_sqft')} sq ft"

    )


    print(

        "\nLAYOUTS TESTED:",
        layout.get(
            "layouts_tested",
            0
        )

    )


    print(

        "VALID LAYOUTS FOUND:",
        layout.get(
            "valid_layouts_found",
            0
        )

    )


    print(

        "LAYOUT VALID:",
        layout.get(
            "layout_valid",
            False
        )

    )


    if layout.get("layout_valid"):

        print(

            "LAYOUT SCORE:",
            layout.get(
                "score",
                0
            )

        )


        print("\nSELECTED FIXTURE POSITIONS:")


        for name, fixture in (
            layout["fixtures"].items()
        ):

            print(

                f"{name.upper():10} -> "
                f"x={fixture['x']}, "
                f"y={fixture['y']}, "
                f"W={fixture['width']}, "
                f"D={fixture['depth']}, "
                f"zone={fixture['wall']}"

            )


    if layout.get("errors"):

        print("\nERRORS:")


        for error in layout["errors"]:

            print(
                "-",
                error
            )