"""
Rich Results validation rules based on Google's official documentation.

This module contains the data-driven ruleset for validating JSON-LD structured data
against Google's requirements for rich results eligibility.

Source of truth: https://developers.google.com/search/docs/appearance/structured-data/search-gallery
Last verified: January 2026
"""

# Google-supported rich result types with required/recommended properties
RICH_RESULTS_RULES = {
    "Article": {
        # https://developers.google.com/search/docs/appearance/structured-data/article
        "required": ["headline"],
        "recommended": ["image", "datePublished", "dateModified", "author"],
        "nested_rules": {
            "author": {
                "recommended": ["name", "url"],
            },
        },
        "description": "News, sports, or blog article rich results",
    },
    "Product": {
        # https://developers.google.com/search/docs/appearance/structured-data/product
        "required": ["name"],
        "recommended": [
            "image",
            "description",
            "offers",
            "aggregateRating",
            "review",
            "brand",
        ],
        "nested_rules": {
            "offers": {
                "required": ["price", "priceCurrency"],
            },
        },
        "description": "Product snippets with pricing and availability",
    },
    "Recipe": {
        # https://developers.google.com/search/docs/appearance/structured-data/recipe
        "required": ["name", "image"],
        "recommended": [
            "author",
            "datePublished",
            "description",
            "prepTime",
            "cookTime",
            "totalTime",
            "recipeYield",
            "recipeIngredient",
            "recipeInstructions",
            "aggregateRating",
            "nutrition",
            "video",
        ],
        "description": "Recipe cards with cook time, ingredients, ratings",
    },
    "FAQPage": {
        # https://developers.google.com/search/docs/appearance/structured-data/faqpage
        "required": ["mainEntity"],
        "recommended": [],
        "nested_rules": {
            "mainEntity": {
                "item_type": "Question",
                "required": ["name", "acceptedAnswer"],
                "nested_rules": {
                    "acceptedAnswer": {
                        "required": ["text"],
                    },
                },
            },
        },
        "note": "Since Aug 2023, only shown for well-known authority sites",
        "description": "FAQ dropdown rich results",
    },
    "Review": {
        # https://developers.google.com/search/docs/appearance/structured-data/review-snippet
        "required": ["itemReviewed", "author"],
        "recommended": ["reviewRating", "datePublished"],
        "nested_rules": {
            "reviewRating": {
                "required": ["ratingValue"],
            },
        },
        "description": "Individual review with star rating",
    },
    "AggregateRating": {
        # Used within other types for star ratings
        "required": ["ratingValue"],
        "recommended": ["ratingCount", "reviewCount", "bestRating", "worstRating"],
        "description": "Average rating from multiple reviews",
    },
    "Event": {
        # https://developers.google.com/search/docs/appearance/structured-data/event
        "required": ["name", "startDate", "location"],
        "recommended": [
            "endDate",
            "description",
            "image",
            "performer",
            "offers",
            "organizer",
        ],
        "nested_rules": {
            "location": {
                "valid_types": ["Place", "VirtualLocation"],
            },
        },
        "description": "Event listings with date and location",
    },
    "VideoObject": {
        # https://developers.google.com/search/docs/appearance/structured-data/video
        "required": ["name", "description", "thumbnailUrl", "uploadDate"],
        "recommended": ["duration", "contentUrl", "embedUrl", "interactionStatistic"],
        "description": "Video rich results with thumbnail and duration",
    },
    "LocalBusiness": {
        # https://developers.google.com/search/docs/appearance/structured-data/local-business
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHours", "image", "priceRange", "geo"],
        "nested_rules": {
            "address": {
                "required": ["streetAddress", "addressLocality", "addressCountry"],
            },
        },
        "description": "Local business information panel",
    },
    "BreadcrumbList": {
        # https://developers.google.com/search/docs/appearance/structured-data/breadcrumb
        "required": ["itemListElement"],
        "recommended": [],
        "nested_rules": {
            "itemListElement": {
                "required": ["position", "name"],
                "recommended": ["item"],
            },
        },
        "description": "Breadcrumb navigation in search results",
    },
    "Organization": {
        # https://developers.google.com/search/docs/appearance/structured-data/organization
        "required": ["name"],
        "recommended": ["url", "logo", "contactPoint", "sameAs"],
        "description": "Organization info for knowledge panels",
    },
}

# Types that are deprecated and should generate warnings
DEPRECATED_TYPES = {
    "HowTo": {
        "deprecated_date": "August 2023",
        "note": "HowTo rich results are no longer shown in Google Search",
        "source": "https://developers.google.com/search/blog/2023/08/howto-faq-changes",
    },
}

# Basic schema types (valid but not rich-result eligible)
# These are informational and don't generate issues
BASIC_SCHEMA_TYPES = {
    "Person",
    "WebSite",
    "WebPage",
    "ImageObject",
    "SearchAction",
    "ItemList",
    "ListItem",
    "Thing",
    "CreativeWork",
    "Offer",
    "Place",
    "PostalAddress",
    "GeoCoordinates",
}

# Subtypes that inherit from rich result types
# Maps subtype -> parent type for validation
SCHEMA_TYPE_INHERITANCE = {
    # Article subtypes
    "NewsArticle": "Article",
    "BlogPosting": "Article",
    "ScholarlyArticle": "Article",
    "TechArticle": "Article",
    "Report": "Article",
    # LocalBusiness subtypes
    "Restaurant": "LocalBusiness",
    "Store": "LocalBusiness",
    "MedicalBusiness": "LocalBusiness",
    "LegalService": "LocalBusiness",
    "FinancialService": "LocalBusiness",
    "FoodEstablishment": "LocalBusiness",
    "LodgingBusiness": "LocalBusiness",
    "SportsActivityLocation": "LocalBusiness",
    "EntertainmentBusiness": "LocalBusiness",
    "HealthAndBeautyBusiness": "LocalBusiness",
    "HomeAndConstructionBusiness": "LocalBusiness",
    "ProfessionalService": "LocalBusiness",
    "AutoRepair": "LocalBusiness",
    # Event subtypes
    "MusicEvent": "Event",
    "SportsEvent": "Event",
    "BusinessEvent": "Event",
    "SaleEvent": "Event",
    "SocialEvent": "Event",
    "TheaterEvent": "Event",
    "EducationEvent": "Event",
    "Festival": "Event",
    # Organization subtypes
    "Corporation": "Organization",
    "EducationalOrganization": "Organization",
    "GovernmentOrganization": "Organization",
    "MedicalOrganization": "Organization",
    "NGO": "Organization",
    "SportsOrganization": "Organization",
}


def get_rules_for_type(schema_type: str) -> dict:
    """
    Get validation rules for a schema type, including inherited types.

    Args:
        schema_type: The @type value from the schema

    Returns:
        Dictionary with validation rules, or empty dict if not a rich result type
    """
    # Check direct match first
    if schema_type in RICH_RESULTS_RULES:
        return RICH_RESULTS_RULES[schema_type]

    # Check for inherited types
    if schema_type in SCHEMA_TYPE_INHERITANCE:
        parent_type = SCHEMA_TYPE_INHERITANCE[schema_type]
        return RICH_RESULTS_RULES.get(parent_type, {})

    return {}


def is_rich_result_type(schema_type: str) -> bool:
    """Check if a schema type is eligible for rich results."""
    return schema_type in RICH_RESULTS_RULES or schema_type in SCHEMA_TYPE_INHERITANCE


def is_deprecated_type(schema_type: str) -> bool:
    """Check if a schema type is deprecated."""
    return schema_type in DEPRECATED_TYPES


def is_basic_type(schema_type: str) -> bool:
    """Check if a schema type is a basic (non-rich-result) type."""
    return schema_type in BASIC_SCHEMA_TYPES


def get_deprecation_info(schema_type: str) -> dict:
    """Get deprecation information for a deprecated type."""
    return DEPRECATED_TYPES.get(schema_type, {})
