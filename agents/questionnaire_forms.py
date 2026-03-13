"""
Collection Brief Questionnaire Form Schemas

Defines the form UI schemas for each question in the collection brief.
"""

from typing import Dict, Any


# Form schemas for each question
QUESTION_FORMS = {
    "collection_snapshot": {
        "id": "collection_snapshot",
        "title": "Let's set the stage",
        "description": "Tell us about your collection basics",
        "sections": [
            {
                "fields": [
                    {
                        "id": "collection_name",
                        "type": "text",
                        "label": "Collection name",
                        "placeholder": "e.g., Sunwashed Commute SS26",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "line",
                        "type": "radio",
                        "label": "Who is this for?",
                        "required": True,
                        "options": [
                            {"label": "Women", "value": "women"},
                            {"label": "Men", "value": "men"},
                            {"label": "Kids", "value": "kids"},
                            {"label": "Unisex", "value": "unisex"}
                        ]
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "season",
                        "type": "radio",
                        "label": "Season & Year",
                        "required": True,
                        "options": [
                            {"label": "SS25", "value": "SS25"},
                            {"label": "AW25", "value": "AW25"},
                            {"label": "SS26", "value": "SS26"},
                            {"label": "AW26", "value": "AW26"},
                            {"label": "SS27", "value": "SS27"}
                        ]
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "launch_window",
                        "type": "radio",
                        "label": "Launch window",
                        "required": True,
                        "options": [
                            {"label": "Jan-Feb", "value": "jan-feb"},
                            {"label": "Mar-Apr", "value": "mar-apr"},
                            {"label": "May-Jun", "value": "may-jun"},
                            {"label": "Jul-Aug", "value": "jul-aug"},
                            {"label": "Sep-Oct", "value": "sep-oct"},
                            {"label": "Nov-Dec", "value": "nov-dec"}
                        ]
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "target_markets",
                        "type": "checkbox",
                        "label": "Target markets",
                        "required": True,
                        "options": [
                            {"label": "India", "value": "india"},
                            {"label": "SEA", "value": "sea"},
                            {"label": "Middle East", "value": "middle-east"},
                            {"label": "Europe", "value": "europe"},
                            {"label": "North America", "value": "north-america"},
                            {"label": "Global", "value": "global"}
                        ]
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "selling_channels",
                        "type": "checkbox",
                        "label": "Selling channels (optional)",
                        "required": False,
                        "options": [
                            {"label": "Online", "value": "online"},
                            {"label": "Retail Stores", "value": "retail"},
                            {"label": "Marketplaces", "value": "marketplaces"},
                            {"label": "D2C", "value": "d2c"}
                        ]
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "customer_persona": {
        "id": "customer_persona",
        "title": "Who are we designing for?",
        "description": "Define your target customer",
        "sections": [
            {
                "fields": [
                    {
                        "id": "persona_description",
                        "type": "textarea",
                        "label": "Customer description",
                        "placeholder": "E.g., Urban working women who want comfort-first but polished outfits for office + after-work plans",
                        "required": True,
                        "rows": 3
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "lifestyle",
                        "type": "text",
                        "label": "Lifestyle / Context",
                        "placeholder": "E.g., working, college, travel, kids play",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "preferences",
                        "type": "text",
                        "label": "Preference hints",
                        "placeholder": "E.g., comfort-first, trend-forward, premium basics",
                        "required": True
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "target_age": {
        "id": "target_age",
        "title": "Target Age Group",
        "description": "What age group is this collection for?",
        "sections": [
            {
                "fields": [
                    {
                        "id": "age_range",
                        "type": "radio",
                        "label": "Primary age range",
                        "required": True,
                        "options": [
                            {"label": "0-5 years", "value": "0-5"},
                            {"label": "6-12 years", "value": "6-12"},
                            {"label": "13-17 years", "value": "13-17"},
                            {"label": "18-24 years", "value": "18-24"},
                            {"label": "25-34 years", "value": "25-34"},
                            {"label": "35-44 years", "value": "35-44"},
                            {"label": "45-54 years", "value": "45-54"},
                            {"label": "55+ years", "value": "55+"}
                        ]
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "creative_north_star": {
        "id": "creative_north_star",
        "title": "Creative North Star",
        "description": "Define the 'feel' and non-negotiables",
        "sections": [
            {
                "fields": [
                    {
                        "id": "emotion",
                        "type": "text",
                        "label": "Emotion to feel (2-4 words)",
                        "placeholder": "E.g., fresh, confident, effortless",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "always_true",
                        "type": "textarea",
                        "label": "Absolutely true in every design (2-3 rules)",
                        "placeholder": "E.g., clean silhouette, comfort mobility, one subtle signature detail",
                        "required": True,
                        "rows": 3
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "range_architecture": {
        "id": "range_architecture",
        "title": "Range Architecture",
        "description": "What are we actually making?",
        "sections": [
            {
                "fields": [
                    {
                        "id": "categories",
                        "type": "textarea",
                        "label": "Categories and style counts",
                        "placeholder": "E.g., Co-ords 18, dresses 22, tops 28, pants 14, light layers 10",
                        "required": True,
                        "rows": 3
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "use_cases",
                        "type": "text",
                        "label": "Key occasions and use-cases",
                        "placeholder": "E.g., workwear, brunch, travel weekend",
                        "required": True
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "fit_guardrails": {
        "id": "fit_guardrails",
        "title": "Fit Guardrails",
        "description": "Sizing and fit intent by category",
        "sections": [
            {
                "fields": [
                    {
                        "id": "size_range",
                        "type": "text",
                        "label": "Size range",
                        "placeholder": "E.g., XS-XXL",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "fit_intent",
                        "type": "textarea",
                        "label": "Fit intent by category",
                        "placeholder": "E.g., Dresses relaxed with optional waist definition, Tops easy fit, slightly boxy",
                        "required": True,
                        "rows": 3
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "design_language": {
        "id": "design_language",
        "title": "Design Language and No-Go's",
        "description": "Signature shapes and what to avoid",
        "sections": [
            {
                "fields": [
                    {
                        "id": "hero_silhouettes",
                        "type": "text",
                        "label": "3 hero silhouettes",
                        "placeholder": "E.g., relaxed shirt dress, boxy co-ord, cropped overshirt",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "avoid_details",
                        "type": "text",
                        "label": "3 details to avoid completely",
                        "placeholder": "E.g., heavy ruffles, deep plunges",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "must_avoid",
                        "type": "text",
                        "label": "Must-avoid list",
                        "placeholder": "E.g., no sheer, no bodycon",
                        "required": True
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "color_materials": {
        "id": "color_materials",
        "title": "Color, Materials, and Surface Direction",
        "description": "The look and tactile feel",
        "sections": [
            {
                "fields": [
                    {
                        "id": "palette",
                        "type": "text",
                        "label": "Palette intent",
                        "placeholder": "E.g., sun-faded neutrals with soft coastal blues",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "handfeel",
                        "type": "text",
                        "label": "Material handfeel direction",
                        "placeholder": "E.g., crisp, breathable",
                        "required": True
                    }
                ]
            },
            {
                "fields": [
                    {
                        "id": "print_role",
                        "type": "text",
                        "label": "Role of prints",
                        "placeholder": "E.g., minimal, 15-20%",
                        "required": True
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "references": {
        "id": "references",
        "title": "References and Assets",
        "description": "Share references that represent what 'right' looks like",
        "sections": [
            {
                "fields": [
                    {
                        "id": "references",
                        "type": "textarea",
                        "label": "At least 3 references (with tags)",
                        "placeholder": "E.g., Ref 1 silhouette: relaxed shirt dress, Ref 2 detailing: pocket geometry",
                        "required": True,
                        "rows": 4
                    }
                ]
            }
        ],
        "submitLabel": "Continue"
    },

    "theme_count": {
        "id": "theme_count",
        "title": "Theme Generation Count",
        "description": "How many theme directions to explore?",
        "sections": [
            {
                "fields": [
                    {
                        "id": "theme_count",
                        "type": "radio",
                        "label": "Number of theme directions",
                        "required": True,
                        "options": [
                            {"label": "1", "value": "1"},
                            {"label": "2", "value": "2"},
                            {"label": "3", "value": "3"},
                            {"label": "4", "value": "4"},
                            {"label": "5", "value": "5"}
                        ]
                    }
                ]
            }
        ],
        "submitLabel": "Complete"
    }
}


def get_form_schema(question_id: str) -> Dict[str, Any]:
    """Get form schema for a question."""
    return QUESTION_FORMS.get(question_id)
