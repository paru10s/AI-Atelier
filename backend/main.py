import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from image_generator import generate_design_image
from recommender import recommend_products
from simple_layout import build_layout
from explorer import build_budget_options
from design_assistant import suggest_edit
from bathroom_analyzer import analyze_bathroom_image
from stability_photo_redesign import generate_photo_redesign

from database import engine
from models import Base


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Kohler AI Designer",
    version="1.0"
)


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# GENERATED IMAGES
# =====================================================

GENERATED_IMAGES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "generated_designs"
)

os.makedirs(
    GENERATED_IMAGES_DIR,
    exist_ok=True
)

app.mount(
    "/images",
    StaticFiles(directory=GENERATED_IMAGES_DIR),
    name="images"
)


# =====================================================
# DATABASE
# =====================================================

Base.metadata.create_all(bind=engine)


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():

    return {
        "message": "Kohler AI Designer Backend Running"
    }


# =====================================================
# REQUEST MODEL
# =====================================================

class DesignRequest(BaseModel):

    room: str
    style: str
    budget: str


class ExploreRequest(BaseModel):

    room: str
    style: str
    budget: str


class AssistantRequest(BaseModel):

    message: str
    room: str
    style: str
    budget: str


class BathroomAnalysisRequest(BaseModel):

    image_base64: str
    mime_type: str


class BathroomRedesignRequest(BaseModel):

    image_base64: str
    mime_type: str
    recommended_style: str = ""
    design_rationale: str = ""
    improvements: list[str] = []


# =====================================================
# ANALYZE EXISTING BATHROOM PHOTO
# =====================================================

@app.post("/analyze-bathroom")
def analyze_bathroom(request: BathroomAnalysisRequest):

    try:

        analysis = analyze_bathroom_image(
            request.image_base64,
            request.mime_type
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except ValueError as error:

        return {
            "success": False,
            "message": str(error),
            "analysis": None
        }

    except Exception as error:

        print("BATHROOM ANALYSIS ERROR:", error)

        return {
            "success": False,
            "message": str(error),
            "analysis": None
        }


# =====================================================
# STABILITY PHOTO-BASED REDESIGN
# Independent from Pollinations / dimensions workflow.
# =====================================================

@app.post("/generate-photo-redesign")
def generate_photo_bathroom_redesign(
    request: BathroomRedesignRequest
):

    try:

        image_path = generate_photo_redesign(
            image_base64=request.image_base64,
            mime_type=request.mime_type,
            recommended_style=request.recommended_style,
            design_rationale=request.design_rationale,
            improvements=request.improvements,
        )

        image_filename = os.path.basename(
            str(image_path).replace("\\", "/")
        )

        return {
            "success": True,
            "image": image_filename,
            "engine": "stability"
        }

    except ValueError as error:

        return {
            "success": False,
            "message": str(error),
            "image": None
        }

    except Exception as error:

        print("STABILITY PHOTO REDESIGN ERROR:", error)

        return {
            "success": False,
            "message": str(error),
            "image": None
        }


# =====================================================
# GENERATE DESIGN
# =====================================================

@app.post("/generate-design")
def generate_design(request: DesignRequest):

    print("\n====================================")
    print("NEW DESIGN REQUEST")
    print("====================================")

    print("Room:", request.room)
    print("Budget:", request.budget)
    print("Theme:", request.style)

    # =================================================
    # STEP 1 — RECOMMEND REAL KOHLER PRODUCTS
    # =================================================

    recommendation = recommend_products(
        request.budget,
        request.style,
        request.room
    )

    if not recommendation["success"]:

        return {
            "success": False,
            "message": recommendation["message"],
            "image": None,
            "products": [],
            "total_product_cost": 0,
            "remaining_budget": request.budget,
            "layout": None
        }

    selected_products = recommendation["products"]

    # Deterministic layout is for the interactive 3D viewer only.
    # It is NOT passed to Pollinations.
    layout = build_layout(
        request.room,
        selected_products
    )

    print("\nSELECTED KOHLER PRODUCTS:")

    for product in selected_products:

        print(
            product["category"],
            "->",
            product["name"],
            "₹",
            product["price"]
        )

    print(
        "TOTAL PRODUCT COST:",
        recommendation["total"]
    )

    print(
        "REMAINING BUDGET:",
        recommendation["remaining_budget"]
    )

    # =================================================
    # STEP 2 — GENERATE PROFESSIONAL AI INTERIOR
    # =================================================

    print(
        "\nGENERATING PROFESSIONAL 3D INTERIOR..."
    )

    image_path = generate_design_image(
        request.room,
        request.budget,
        request.style,
        selected_products
    )

    print(
        "RETURNED IMAGE PATH:",
        image_path
    )

    # =================================================
    # STEP 3 — RETURN RESULT
    # =================================================

    # Always return only the generated filename.
    # This avoids Windows backslash / nested-path URL problems.
    image_filename = os.path.basename(
        str(image_path).replace("\\", "/")
    )

    return {
        "success": True,
        "room": request.room,
        "budget": request.budget,
        "theme": request.style,
        "image": image_filename,
        "products": selected_products,
        "total_product_cost": recommendation["total"],
        "remaining_budget": recommendation["remaining_budget"],
        "layout": layout
    }


# =====================================================
# BUDGET TRADE-OFF EXPLORER
# =====================================================

@app.post("/explore")
def explore(request: ExploreRequest):

    options = build_budget_options(
        request.budget,
        request.style,
        request.room
    )

    return {
        "success": True,
        "options": options
    }


# =====================================================
# DESIGN ASSISTANT
# =====================================================

@app.post("/design-assistant")
def design_assistant(request: AssistantRequest):

    result = suggest_edit(
        request.message,
        request.budget,
        request.style
    )

    return {
        **result,
        "room": request.room
    }
