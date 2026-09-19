from PIL import Image, ImageDraw, ImageFont
import os


# =====================================================
# SETTINGS
# =====================================================

CANVAS_SIZE = 1024
PADDING = 80

BACKGROUND = "white"
ROOM_COLOR = "white"
WALL_COLOR = "black"

FIXTURE_COLORS = {
    "basin": "#9ED2FF",
    "toilet": "#FFD89E",
    "shower": "#B6F2C2",
    "bathtub": "#E3C2FF"
}


# =====================================================
# GENERATE FLOOR PLAN REFERENCE
# =====================================================

def render_layout_reference(layout):

    if not layout.get("layout_valid"):

        raise Exception(
            "Cannot render an invalid layout."
        )

    room = layout["room"]

    room_width = room["width_ft"]
    room_depth = room["depth_ft"]

    fixtures = layout["fixtures"]


    # =================================================
    # CREATE IMAGE
    # =================================================

    image = Image.new(
        "RGB",
        (CANVAS_SIZE, CANVAS_SIZE),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)


    # =================================================
    # SCALE ROOM TO IMAGE
    # =================================================

    available_width = (
        CANVAS_SIZE - (PADDING * 2)
    )

    available_height = (
        CANVAS_SIZE - (PADDING * 2)
    )


    scale_x = (
        available_width / room_width
    )

    scale_y = (
        available_height / room_depth
    )


    scale = min(
        scale_x,
        scale_y
    )


    rendered_width = (
        room_width * scale
    )

    rendered_depth = (
        room_depth * scale
    )


    room_left = (
        CANVAS_SIZE - rendered_width
    ) / 2

    room_top = (
        CANVAS_SIZE - rendered_depth
    ) / 2


    room_right = (
        room_left + rendered_width
    )

    room_bottom = (
        room_top + rendered_depth
    )


    # =================================================
    # DRAW ROOM
    # =================================================

    draw.rectangle(
        [
            room_left,
            room_top,
            room_right,
            room_bottom
        ],
        fill=ROOM_COLOR,
        outline=WALL_COLOR,
        width=8
    )


    # =================================================
    # COORDINATE CONVERSION
    #
    # Layout engine:
    # (0,0) = front-left
    #
    # Image:
    # top of image = back of bathroom
    # bottom = front / entrance
    # =================================================

    def convert_fixture(fixture):

        x = fixture["x"]
        y = fixture["y"]

        width = fixture["width"]
        depth = fixture["depth"]


        px1 = (
            room_left
            + x * scale
        )


        # Flip Y axis so rear of room
        # appears at top of floor plan.

        py1 = (
            room_bottom
            - (y + depth) * scale
        )


        px2 = (
            px1
            + width * scale
        )


        py2 = (
            py1
            + depth * scale
        )


        return (
            px1,
            py1,
            px2,
            py2
        )


    # =================================================
    # DRAW FIXTURES
    # =================================================

    for name, fixture in fixtures.items():

        box = convert_fixture(
            fixture
        )


        color = FIXTURE_COLORS.get(
            name,
            "#DDDDDD"
        )


        draw.rectangle(
            box,
            fill=color,
            outline="black",
            width=4
        )


        label = name.upper()


        center_x = (
            box[0] + box[2]
        ) / 2


        center_y = (
            box[1] + box[3]
        ) / 2


        # Approximate text positioning
        text_x = (
            center_x
            - len(label) * 4
        )

        text_y = (
            center_y - 6
        )


        draw.text(
            (text_x, text_y),
            label,
            fill="black"
        )


    # =================================================
    # DRAW FRONT / ENTRANCE LABEL
    # =================================================

    draw.text(
        (
            room_left,
            room_bottom + 20
        ),
        "FRONT / ENTRANCE",
        fill="black"
    )


    # =================================================
    # ROOM DIMENSION LABEL
    # =================================================

    dimension_text = (
        f"{room_width} ft x "
        f"{room_depth} ft"
    )


    draw.text(
        (
            room_left,
            room_top - 30
        ),
        dimension_text,
        fill="black"
    )


    # =================================================
    # SAVE
    # =================================================

    folder = "layout_references"

    os.makedirs(
        folder,
        exist_ok=True
    )


    existing = [

        file

        for file in os.listdir(folder)

        if file.lower().endswith(
            ".png"
        )

    ]


    number = len(existing) + 1


    filename = (
        f"layout_{number}.png"
    )


    filepath = os.path.join(
        folder,
        filename
    )


    image.save(filepath)


    print(
        "\nLAYOUT REFERENCE CREATED:"
    )

    print(filepath)


    return 
