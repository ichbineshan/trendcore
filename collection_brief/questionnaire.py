"""
Collection Brief Questionnaire

Defines the 10 questions for collection onboarding.
"""

from typing import Dict, Any


COLLECTION_BRIEF_QUESTIONS = [
    {
        "id": "collection_snapshot",
        "number": 1,
        "title": "Collection Snapshot",
        "prompt": "In 1–2 lines, tell me what collection we're building. This sets the base context for everything that follows.",
        "what_to_include": [
            "Line: Men / Women / Kids (pick one)",
            "Season + year (eg SS26, AW26)",
            "Launch window (eg May–June 2026, capture only)",
            "Target regions (we'll suggest based on Brand Identity, you just confirm)"
        ],
        "example": "Women, SS26, May–June 2026, India + SEA"
    },
    {
        "id": "customer_persona",
        "number": 2,
        "title": "Customer Persona",
        "prompt": "Who exactly are we designing for? Think about the real customer and their lifestyle.",
        "what_to_include": [
            "A simple description of the customer in plain words",
            "Lifestyle or context (eg working, college, travel, kids play)",
            "Preference hints (eg comfort-first, trend-forward, premium basics)"
        ],
        "example": "Urban working women who want comfort-first but polished outfits for office + after-work plans"
    },
    {
        "id": "target_age",
        "number": 3,
        "title": "Target Age",
        "prompt": "What age group is this collection primarily for?",
        "what_to_include": [
            "One primary age range",
            "For Kids, share age in years"
        ],
        "example": "Primary: 25–34"
    },
    {
        "id": "creative_north_star",
        "number": 4,
        "title": "Creative North Star",
        "prompt": "Define the 'feel' and the non-negotiables. These are rules the AI will follow.",
        "what_to_include": [
            "Emotion to feel (2–4 words)",
            "Absolutely true in every design (2–3 rules)"
        ],
        "example": "Emotion: fresh, confident, effortless\nAlways true: clean silhouette, comfort mobility, one subtle signature detail"
    },
    {
        "id": "range_architecture",
        "number": 5,
        "title": "Range Architecture",
        "prompt": "What are we actually making? List your categories and rough counts.",
        "what_to_include": [
            "Categories you want in the collection",
            "Approx style count per category",
            "Key occasions and use-cases"
        ],
        "example": "Co-ords 18, dresses 22, tops 28, pants 14, light layers 10\nUse-cases: workwear, brunch, travel weekend"
    },
    {
        "id": "fit_guardrails",
        "number": 6,
        "title": "Fit Guardrails",
        "prompt": "Tell me sizing and fit intent by category.",
        "what_to_include": [
            "Size range",
            "Fit intent by category"
        ],
        "example": "Sizes: XS–XXL\nDresses relaxed with optional waist definition\nTops easy fit, slightly boxy"
    },
    {
        "id": "design_language",
        "number": 7,
        "title": "Design Language and No-Go's",
        "prompt": "Define your signature shapes and what we should never generate.",
        "what_to_include": [
            "3 hero silhouettes",
            "3 details to avoid completely",
            "Must-avoid list"
        ],
        "example": "Hero: relaxed shirt dress, boxy co-ord, cropped overshirt\nAvoid: heavy ruffles, deep plunges\nMust-avoid: no sheer, no bodycon"
    },
    {
        "id": "color_materials",
        "number": 8,
        "title": "Color, Materials, and Surface Direction",
        "prompt": "Describe the look and tactile feel.",
        "what_to_include": [
            "Palette intent",
            "Material handfeel direction",
            "Role of prints"
        ],
        "example": "Palette: sun-faded neutrals with soft coastal blues\nHandfeel: crisp, breathable\nPrint role: minimal, 15-20%"
    },
    {
        "id": "references",
        "number": 9,
        "title": "References and Assets",
        "prompt": "Share references that represent what 'right' looks like.",
        "what_to_include": [
            "At least 3 references",
            "Tag each reference"
        ],
        "example": "Ref 1 silhouette: relaxed shirt dress\nRef 2 detailing: pocket geometry"
    },
    {
        "id": "theme_count",
        "number": 10,
        "title": "Theme Generation Count",
        "prompt": "How many different theme directions do you want to explore?",
        "what_to_include": [
            "Pick one number: 1, 2, 3, 4, 5"
        ],
        "example": "3"
    }
]


def get_question_by_number(number: int) -> Dict[str, Any]:
    """Get question by number (1-10)."""
    for q in COLLECTION_BRIEF_QUESTIONS:
        if q["number"] == number:
            return q
    return None


def get_question_by_id(question_id: str) -> Dict[str, Any]:
    """Get question by ID."""
    for q in COLLECTION_BRIEF_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


def get_total_questions() -> int:
    """Get total number of questions."""
    return len(COLLECTION_BRIEF_QUESTIONS)
