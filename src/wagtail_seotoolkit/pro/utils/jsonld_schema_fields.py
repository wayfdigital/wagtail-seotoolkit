# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
JSON-LD schema field definitions.

Defines the commonly-used fields for each schema type, organized by
required, recommended, and optional categories.

Licensed under the WAYF Proprietary License.
"""

# Schema field definitions per type
# Only includes commonly-used fields to avoid overwhelming users
SCHEMA_FIELDS = {
    # Content Types
    "Article": {
        "required": ["headline", "author", "datePublished"],
        "recommended": [
            "dateModified",
            "image",
            "publisher",
            "description",
            "articleBody",
        ],
        "optional": ["speakable", "keywords", "wordCount", "articleSection"],
    },
    "BlogPosting": {
        "required": ["headline", "author", "datePublished"],
        "recommended": [
            "dateModified",
            "image",
            "publisher",
            "description",
            "articleBody",
        ],
        "optional": ["speakable", "keywords", "wordCount", "mainEntityOfPage"],
    },
    "NewsArticle": {
        "required": ["headline", "author", "datePublished"],
        "recommended": [
            "dateModified",
            "image",
            "publisher",
            "description",
            "dateline",
        ],
        "optional": ["speakable", "keywords", "printEdition", "printSection"],
    },
    "Report": {
        "required": ["name", "author", "datePublished"],
        "recommended": ["description", "publisher", "about", "encoding"],
        "optional": ["keywords", "pagination", "reportNumber"],
    },
    "ScholarlyArticle": {
        "required": ["headline", "author", "datePublished"],
        "recommended": ["publisher", "description", "about", "citation"],
        "optional": ["speakable", "keywords", "pageStart", "pageEnd"],
    },
    "DigitalDocument": {
        "required": ["name"],
        "recommended": ["author", "datePublished", "description", "encoding"],
        "optional": ["hasDigitalDocumentPermission"],
    },
    "FAQPage": {
        "required": ["mainEntity"],  # List of Question/Answer
        "recommended": ["name", "description"],
        "optional": ["audience", "about"],
    },
    "CreativeWork": {
        "required": ["name"],
        "recommended": ["author", "datePublished", "description"],
        "optional": ["keywords", "about", "genre"],
    },
    # Organization & People
    "Organization": {
        "required": ["name"],
        "recommended": [
            "url",
            "logo",
            "description",
            "address",
            "contactPoint",
            "sameAs",
        ],
        "optional": ["foundingDate", "email", "telephone", "numberOfEmployees"],
    },
    "GovernmentOrganization": {
        "required": ["name"],
        "recommended": ["url", "description", "address", "contactPoint"],
        "optional": ["areaServed", "member", "memberOf"],
    },
    "FinancialService": {
        "required": ["name"],
        "recommended": ["url", "description", "address", "telephone"],
        "optional": ["openingHours", "currenciesAccepted", "paymentAccepted"],
    },
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "jobTitle", "worksFor"],
        "optional": ["email", "telephone", "sameAs", "alumniOf"],
    },
    # Location
    "Country": {
        "required": ["name"],
        "recommended": ["url", "description"],
        "optional": ["containsPlace", "geo"],
    },
    "Place": {
        "required": ["name"],
        "recommended": ["address", "geo", "description"],
        "optional": ["telephone", "openingHoursSpecification"],
    },
    # Financial
    "MonetaryGrant": {
        "required": ["name", "funder"],
        "recommended": ["amount", "description"],
        "optional": ["fundedItem", "sponsor"],
    },
    "Project": {
        "required": ["name"],
        "recommended": ["description", "funder", "member"],
        "optional": ["startDate", "endDate", "budget"],
    },
    # Site Structure
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["potentialAction"],  # SearchAction
        "optional": ["inLanguage", "publisher", "description"],
    },
    "WebPage": {
        "required": ["name"],
        "recommended": ["description", "breadcrumb", "mainEntity"],
        "optional": ["datePublished", "dateModified", "inLanguage"],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],  # List of ListItem
        "recommended": [],
        "optional": [],
    },
}


# Nested type field definitions (for expandable sub-forms)
NESTED_TYPE_FIELDS = {
    "Person": ["name", "url", "image", "jobTitle", "worksFor", "sameAs"],
    "ImageObject": ["url", "width", "height", "caption"],
    "PostalAddress": [
        "streetAddress",
        "addressLocality",
        "addressRegion",
        "postalCode",
        "addressCountry",
    ],
    "ContactPoint": [
        "telephone",
        "email",
        "contactType",
        "areaServed",
        "availableLanguage",
    ],
    "Organization": ["name", "url", "logo"],  # Simplified for nesting
    "MonetaryAmount": ["value", "currency"],
    "Place": ["name", "address", "geo"],
    "SearchAction": ["target", "query-input"],
    "ListItem": ["position", "name", "item"],
}


# Fields that support multiple values (repeatable in UI)
REPEATABLE_FIELDS = [
    "author",
    "creator",
    "contributor",
    "contactPoint",
    "sameAs",
    "image",
    "mainEntity",
    "member",
    "funder",
    "sponsor",
]


# Default field mappings for common patterns
# These are suggested placeholders for each property
DEFAULT_FIELD_MAPPINGS = {
    "headline": "{title}",
    "name": "{title}",
    "description": "{search_description}",
    "datePublished": "{first_published_at}",
    "dateModified": "{last_published_at}",
    "url": "{full_url}",
    "articleBody": "{body}",
    "wordCount": "{body_word_count}",
}


# Schema type categories for UI organization
SCHEMA_TYPE_CATEGORIES = {
    "Content Types": [
        "Article",
        "BlogPosting",
        "NewsArticle",
        "Report",
        "ScholarlyArticle",
        "DigitalDocument",
        "FAQPage",
        "CreativeWork",
    ],
    "Organization & People": [
        "Organization",
        "GovernmentOrganization",
        "FinancialService",
        "Person",
    ],
    "Location": [
        "Country",
        "Place",
    ],
    "Financial": [
        "MonetaryGrant",
        "Project",
    ],
    "Site Structure": [
        "WebSite",
        "WebPage",
        "BreadcrumbList",
    ],
}


def get_schema_fields(schema_type):
    """
    Get field definitions for a specific schema type.

    Args:
        schema_type: The JSON-LD schema type (e.g., 'Article', 'BlogPosting')

    Returns:
        Dict with 'required', 'recommended', 'optional' field lists,
        or empty dict if schema type not found.
    """
    return SCHEMA_FIELDS.get(
        schema_type, {"required": [], "recommended": [], "optional": []}
    )


def get_nested_type_fields(nested_type):
    """
    Get field definitions for a nested type.

    Args:
        nested_type: The nested type name (e.g., 'Person', 'ImageObject')

    Returns:
        List of field names for the nested type.
    """
    return NESTED_TYPE_FIELDS.get(nested_type, [])


def is_repeatable_field(field_name):
    """
    Check if a field supports multiple values.

    Args:
        field_name: The property name to check

    Returns:
        True if the field can have multiple values.
    """
    return field_name in REPEATABLE_FIELDS


def get_default_mapping(field_name):
    """
    Get the default placeholder mapping for a field.

    Args:
        field_name: The schema.org property name

    Returns:
        Default placeholder string (e.g., '{title}') or None.
    """
    return DEFAULT_FIELD_MAPPINGS.get(field_name)





