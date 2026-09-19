import os
import base64
import requests
from io import BytesIO
from urllib.parse import quote

from PIL import Image, ImageDraw
from dotenv import load_dotenv


# =====================================================
# ENVIRONMENT / OUTPUT
# =====================================================

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

GENERATED_FOLDER = "generated_designs"
REFERENCE_FOLDER = "layout_references"

os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(REFERENCE_FOLDER, exist_ok=True)


# =====================================================
# PRODUCT HELPERS
# =====================================================

def get_product(selected_products, category):
    category = category.lower()

    for product in selected_products:
        if str(product.get("category", "")).lower() == category:
            return product

    return None


def get_inventory(selected_products):
    categories = {
        str(product.get("category", "")).lower()
        for product in selected_products
    }

    return {
        "basin": "basin" in categories,
        "faucet": "faucet" in categories,
        "toilet": "toilet" in categories,
        "shower": "shower" in categories,
        "bathtub": "bathtub" in categories,
    }


def build_product_text(selected_products):
    lines = []

    for product in selected_products:
        category = str(product.get("category", "fixture")).upper()
        name = product.get("name", "Kohler fixture")
        lines.append(f"- {category}: {name}")

    return "\n".join(lines)


# =====================================================
# SIMPLE CONTROLLED 3D REFERENCE
# =====================================================

def _quad(draw, points, fill, outline=(80, 80, 80), width=4):
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width)


def _box(draw, x1, y1, x2, y2, height, fill):
    """
    Draw a simple pseudo-3D box whose footprint is x1,y1,x2,y2.
    This is intentionally clean and object-count controlled.
    """
    top_shift = max(10, int(height * 0.35))

    front = [
        (x1, y1),
        (x2, y1),
        (x2, y2),
        (x1, y2),
    ]

    top = [
        (x1, y1),
        (x2, y1),
        (x2, y1 - top_shift),
        (x1, y1 - top_shift),
    ]

    side = [
        (x2, y1),
        (x2, y2),
        (x2, y2 - top_shift),
        (x2, y1 - top_shift),
    ]

    _quad(draw, front, fill)
    _quad(draw, top, tuple(min(c + 22, 255) for c in fill))
    _quad(draw, side, tuple(max(c - 20, 0) for c in fill))


def create_controlled_3d_reference(selected_products):
    """
    Creates ONE automatic perspective-room reference.

    Important:
    - no drag/drop coordinates
    - exactly one visual placeholder per selected sanitary fixture
    - fixtures are deliberately distributed across multiple walls/zones
    - the image model receives this instead of inventing the whole layout
    """

    inventory = get_inventory(selected_products)

    W = 1024
    H = 1024

    image = Image.new("RGB", (W, H), (238, 232, 224))
    draw = ImageDraw.Draw(image)

    # -------------------------------------------------
    # ROOM SHELL — perspective corner room
    # -------------------------------------------------

    ceiling_y = 90
    back_y = 270
    floor_front_y = 930

    back_left = 250
    back_right = 785
    front_left = 55
    front_right = 970

    # Back wall
    draw.polygon(
        [
            (back_left, ceiling_y),
            (back_right, ceiling_y),
            (back_right, back_y),
            (back_left, back_y),
        ],
        fill=(232, 220, 210)
    )

    # Left wall
    draw.polygon(
        [
            (0, 0),
            (back_left, ceiling_y),
            (back_left, back_y),
            (front_left, floor_front_y),
            (0, H),
        ],
        fill=(225, 213, 203)
    )

    # Right wall
    draw.polygon(
        [
            (back_right, ceiling_y),
            (W, 0),
            (W, H),
            (front_right, floor_front_y),
            (back_right, back_y),
        ],
        fill=(218, 207, 198)
    )

    # Floor
    draw.polygon(
        [
            (back_left, back_y),
            (back_right, back_y),
            (front_right, floor_front_y),
            (front_left, floor_front_y),
        ],
        fill=(207, 194, 180)
    )

    # Ceiling
    draw.polygon(
        [
            (0, 0),
            (W, 0),
            (back_right, ceiling_y),
            (back_left, ceiling_y),
        ],
        fill=(244, 240, 235)
    )

    # Room edges
    edge = (125, 115, 108)
    draw.line([(back_left, ceiling_y), (back_left, back_y)], fill=edge, width=4)
    draw.line([(back_right, ceiling_y), (back_right, back_y)], fill=edge, width=4)
    draw.line([(back_left, back_y), (front_left, floor_front_y)], fill=edge, width=4)
    draw.line([(back_right, back_y), (front_right, floor_front_y)], fill=edge, width=4)

    # Window on back wall — decorative architectural anchor.
    draw.rectangle(
        (440, 125, 610, 235),
        fill=(190, 215, 222),
        outline=(105, 115, 118),
        width=4
    )
    draw.line((525, 125, 525, 235), fill=(120, 130, 132), width=3)

    # -------------------------------------------------
    # WASH STATION — LEFT SIDE / MID-DEPTH
    # -------------------------------------------------

    if inventory["basin"]:
        # Vanity cabinet
        _box(
            draw,
            125, 500,
            340, 650,
            95,
            (183, 154, 135)
        )

        # Counter
        draw.polygon(
            [
                (118, 492),
                (345, 492),
                (340, 520),
                (125, 520),
            ],
            fill=(238, 232, 222),
            outline=(90, 90, 90)
        )

        # ONE basin
        draw.ellipse(
            (180, 485, 285, 535),
            fill=(247, 247, 244),
            outline=(90, 90, 90),
            width=4
        )

        # Mirror above vanity
        draw.rounded_rectangle(
            (150, 300, 315, 460),
            radius=20,
            fill=(205, 218, 219),
            outline=(100, 100, 100),
            width=4
        )

        # ONE faucet marker
        if inventory["faucet"]:
            draw.line((232, 480, 232, 450), fill=(95, 95, 95), width=7)
            draw.line((232, 450, 255, 450), fill=(95, 95, 95), width=7)

    # -------------------------------------------------
    # SHOWER — BACK-RIGHT CORNER
    # -------------------------------------------------

    if inventory["shower"]:
        # Shower tray
        _quad(
            draw,
            [
                (610, 360),
                (770, 350),
                (850, 535),
                (650, 550),
            ],
            (205, 220, 220),
            outline=(85, 105, 108),
            width=4
        )

        # Glass panels — one enclosure, not a second shower
        draw.polygon(
            [
                (610, 185),
                (770, 180),
                (770, 350),
                (610, 360),
            ],
            fill=(218, 232, 233),
            outline=(90, 110, 115)
        )
        draw.polygon(
            [
                (770, 180),
                (850, 255),
                (850, 535),
                (770, 350),
            ],
            fill=(210, 227, 229),
            outline=(90, 110, 115)
        )

        # Single shower head
        draw.line((735, 225, 735, 285), fill=(90, 90, 90), width=7)
        draw.line((735, 225, 770, 225), fill=(90, 90, 90), width=7)
        draw.ellipse((760, 216, 790, 234), fill=(110, 110, 110))

    # -------------------------------------------------
    # TOILET — RIGHT SIDE / MID-FOREGROUND
    # -------------------------------------------------

    if inventory["toilet"]:
        # ONE unmistakable toilet silhouette
        draw.rounded_rectangle(
            (700, 600, 815, 675),
            radius=30,
            fill=(246, 246, 242),
            outline=(90, 90, 90),
            width=4
        )
        draw.ellipse(
            (685, 645, 835, 770),
            fill=(248, 248, 245),
            outline=(90, 90, 90),
            width=4
        )
        draw.ellipse(
            (712, 670, 808, 742),
            fill=(220, 222, 219),
            outline=(110, 110, 110),
            width=3
        )

    # -------------------------------------------------
    # BATHTUB — BACK/LEFT-CENTRE, FAR FROM TOILET
    # -------------------------------------------------

    if inventory["bathtub"]:
        # ONE large adult bathtub. Large rectangular outer body with
        # one inner cavity makes it much less likely to be read as
        # multiple small tubs/bowls.
        tub_outer = [
            (345, 585),
            (600, 570),
            (670, 720),
            (370, 745),
        ]

        tub_inner = [
            (390, 615),
            (570, 605),
            (615, 690),
            (405, 708),
        ]

        _quad(
            draw,
            tub_outer,
            (244, 243, 238),
            outline=(90, 90, 90),
            width=5
        )

        _quad(
            draw,
            tub_inner,
            (195, 216, 220),
            outline=(115, 115, 115),
            width=4
        )

    # -------------------------------------------------
    # DECOR PLACEHOLDERS — NON-SANITARY ONLY
    # -------------------------------------------------

    # Rug
    draw.ellipse(
        (360, 790, 640, 900),
        fill=(194, 170, 158),
        outline=(150, 130, 120)
    )

    # Plant in one corner
    draw.rectangle(
        (835, 500, 880, 565),
        fill=(165, 135, 112),
        outline=(95, 85, 75)
    )
    for dx, dy in [
        (-28, -45),
        (0, -70),
        (30, -50),
        (-10, -95),
        (22, -92)
    ]:
        draw.ellipse(
            (
                850 + dx,
                505 + dy,
                885 + dx,
                555 + dy
            ),
            fill=(105, 137, 103),
            outline=(75, 105, 75)
        )

    existing = [
        f for f in os.listdir(REFERENCE_FOLDER)
        if f.lower().endswith(".png")
    ]

    filename = f"controlled_3d_{len(existing) + 1}.png"
    path = os.path.join(REFERENCE_FOLDER, filename)

    image.save(path)

    return path


# =====================================================
# POLLINATIONS IMAGE EDIT
# =====================================================

def call_image_edit(reference_path, prompt):
    """
    The model is no longer asked to invent the bathroom structure from
    nothing. It receives a controlled 3D room composition with one
    placeholder per selected sanitary fixture and is asked to transform
    it into a professional photograph.
    """

    url = "https://gen.pollinations.ai/v1/images/edits"

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    data = {
        "model": "kontext",
        "prompt": prompt,
        "size": "1024x1024",
        "quality": "high",
        "response_format": "b64_json",
    }

    with open(reference_path, "rb") as image_file:
        files = {
            "image": (
                os.path.basename(reference_path),
                image_file,
                "image/png"
            )
        }

        response = requests.post(
            url,
            headers=headers,
            data=data,
            files=files,
            timeout=300
        )

    print("POLLINATIONS STATUS:", response.status_code)

    if response.status_code != 200:
        print("POLLINATIONS ERROR:")
        print(response.text)

        raise Exception(
            "Pollinations controlled image edit failed: "
            f"{response.status_code}"
        )

    result = response.json()

    if "data" not in result or not result["data"]:
        raise Exception("Pollinations returned no image.")

    result_image = result["data"][0]

    if result_image.get("b64_json"):
        image_bytes = base64.b64decode(result_image["b64_json"])
        return Image.open(BytesIO(image_bytes)).convert("RGB")

    if result_image.get("url"):
        image_response = requests.get(
            result_image["url"],
            timeout=180
        )
        image_response.raise_for_status()
        return Image.open(
            BytesIO(image_response.content)
        ).convert("RGB")

    raise Exception("Pollinations returned no usable image.")


# =====================================================
# GENERATE DESIGN
# =====================================================

def generate_design_image(
    room,
    budget,
    theme,
    selected_products
):
    print("\n====================================")
    print("FREEFORM 3D BATHROOM GENERATION")
    print("====================================")

    if not POLLINATIONS_API_KEY:
        raise Exception(
            "POLLINATIONS_API_KEY not found in .env file"
        )

    inventory = get_inventory(selected_products)
    product_text = build_product_text(selected_products)

    print("FIXTURE INVENTORY:", inventory)

    has_basin = inventory["basin"]
    has_toilet = inventory["toilet"]
    has_shower = inventory["shower"]
    has_bathtub = inventory["bathtub"]

    prompt = f"""
Create ONE photorealistic 3D luxury bathroom interior.

Room: {room}
Budget: ₹{budget}
Theme: {theme}

Selected Kohler products:
{product_text}

Create a realistic 3D architectural bathroom with strong depth, correct scale, visible floor, and at least 2 intersecting walls.
Use a diagonal three-quarter camera perspective.
Do not create a flat front view or place every fixture on one wall.

STRICT FIXTURE COUNT:
{"Exactly ONE wash station: ONE vanity + ONE basin + ONE faucet together." if has_basin else "NO basin, vanity, or faucet."}
{"Exactly ONE toilet." if has_toilet else "NO toilet."}
{"Exactly ONE shower zone." if has_shower else "NO shower."}
{"Exactly ONE bathtub." if has_bathtub else "NO bathtub."}

ABSOLUTELY NO DUPLICATE FIXTURES.
Never create a second basin, vanity, faucet, toilet, shower, or bathtub.
Each selected sanitary product must appear exactly once.

Make the bathroom luxurious, spacious, professionally designed, and Kohler-inspired.
Add tasteful non-plumbing decor such as mirrors, warm lighting, towels, plants, rug, shelves, niche, and accessories.

High-end 3D architectural visualization with realistic stone, ceramic, glass, metal, wood, reflections, shadows, and natural lighting.
Magazine-quality luxury bathroom photography.

No text, labels, dimensions, arrows, prices, product names, people, or annotations.
"""

    print("final prompt --> " + prompt)

    image = call_image_generate(prompt)

    filepath = save_image(image)

    print("FINAL IMAGE:", filepath)

    return filepath



# =====================================================
# SAVE IMAGE
# =====================================================



def call_image_generate(prompt):
    encoded_prompt = quote(prompt)

    url = (
        f"https://gen.pollinations.ai/image/{encoded_prompt}"
        "?model=flux"
        "&width=1024"
        "&height=1024"
    )

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=180
    )

    print("POLLINATIONS STATUS:", response.status_code)

    if response.status_code != 200:
        print("POLLINATIONS ERROR:")
        print(response.text)
        raise Exception(
            f"Pollinations image generation failed: {response.status_code}"
        )

    image = Image.open(BytesIO(response.content))
    return image


def save_image(image):
    existing_images = [
        f for f in os.listdir(GENERATED_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    filename = f"design_{len(existing_images) + 1}.png"
    filepath = os.path.join(GENERATED_FOLDER, filename)

    if image.mode != "RGB":
        image = image.convert("RGB")

    image.save(filepath, format="PNG")

    return filepath
