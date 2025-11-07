"""
Reusable SEO validation utilities for core checkers.

This module provides reusable functions for validating SEO metadata
(titles and meta descriptions) that can be used by checkers, API endpoints,
and other components.

Licensed under the MIT License. See LICENSE-MIT for details.
"""

from typing import Dict, List

# Title tag constraints
TITLE_MIN_LENGTH = 50
TITLE_MAX_LENGTH = 60

# Meta description constraints
META_DESC_MIN_LENGTH = 120
META_DESC_MAX_LENGTH = 160

# CTA keywords for meta descriptions
CTA_KEYWORDS = [
    "buy",
    "learn",
    "discover",
    "get",
    "find",
    "explore",
    "download",
    "try",
    "start",
    "join",
]


def validate_title(title: str) -> Dict[str, any]:
    """
    Validate an SEO title and return validation results.

    Args:
        title: The title string to validate

    Returns:
        Dict with validation results:
        {
            "is_valid": bool,
            "length": int,
            "issues": [
                {
                    "type": "missing|too_short|too_long",
                    "severity": "high|medium|low",
                    "message": "Description of the issue"
                }
            ]
        }
    """
    issues = []

    # Check if title is missing or empty
    if not title or not title.strip():
        return {
            "is_valid": False,
            "length": 0,
            "issues": [
                {
                    "type": "missing",
                    "severity": "high",
                    "message": "Title tag is missing or empty.",
                }
            ],
        }

    # Normalize whitespace
    title_text = " ".join(title.strip().split())
    title_length = len(title_text)

    # Check length
    if title_length < TITLE_MIN_LENGTH:
        issues.append(
            {
                "type": "too_short",
                "severity": "medium",
                "message": f"Title is too short ({title_length} chars). Should be between {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH} characters.",
            }
        )
    elif title_length > TITLE_MAX_LENGTH:
        issues.append(
            {
                "type": "too_long",
                "severity": "medium",
                "message": f"Title is too long ({title_length} chars). Should be between {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH} characters.",
            }
        )

    return {"is_valid": len(issues) == 0, "length": title_length, "issues": issues}


def validate_meta_description(description: str) -> Dict[str, any]:
    """
    Validate a meta description and return validation results.

    Args:
        description: The meta description string to validate

    Returns:
        Dict with validation results:
        {
            "is_valid": bool,
            "length": int,
            "has_cta": bool,
            "issues": [
                {
                    "type": "missing|too_short|too_long|no_cta",
                    "severity": "high|medium|low",
                    "message": "Description of the issue"
                }
            ]
        }
    """
    issues = []

    # Check if description is missing or empty
    if not description or not description.strip():
        return {
            "is_valid": False,
            "length": 0,
            "has_cta": False,
            "issues": [
                {
                    "type": "missing",
                    "severity": "high",
                    "message": "Meta description is missing or empty.",
                }
            ],
        }

    desc_text = description.strip()
    desc_length = len(desc_text)

    # Check length
    if desc_length < META_DESC_MIN_LENGTH:
        issues.append(
            {
                "type": "too_short",
                "severity": "medium",
                "message": f"Meta description is too short ({desc_length} chars). Should be between {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH} characters.",
            }
        )
    elif desc_length > META_DESC_MAX_LENGTH:
        issues.append(
            {
                "type": "too_long",
                "severity": "medium",
                "message": f"Meta description is too long ({desc_length} chars). Should be between {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH} characters.",
            }
        )

    # Check for CTA words
    has_cta = any(word in desc_text.lower() for word in CTA_KEYWORDS)
    if not has_cta:
        issues.append(
            {
                "type": "no_cta",
                "severity": "low",
                "message": f"Consider adding a call-to-action (e.g., {', '.join(CTA_KEYWORDS[:5])}).",
            }
        )

    return {
        "is_valid": len([i for i in issues if i["severity"] in ["high", "medium"]])
        == 0,
        "length": desc_length,
        "has_cta": has_cta,
        "issues": issues,
    }


def get_validation_summary(validation_result: Dict[str, any]) -> str:
    """
    Get a human-readable summary of validation results.

    Args:
        validation_result: Result from validate_title or validate_meta_description

    Returns:
        String summary of validation status
    """
    if validation_result["is_valid"]:
        return "✓ Valid"

    high_severity_count = sum(
        1 for issue in validation_result["issues"] if issue["severity"] == "high"
    )
    medium_severity_count = sum(
        1 for issue in validation_result["issues"] if issue["severity"] == "medium"
    )
    low_severity_count = sum(
        1 for issue in validation_result["issues"] if issue["severity"] == "low"
    )

    parts = []
    if high_severity_count:
        parts.append(f"{high_severity_count} critical")
    if medium_severity_count:
        parts.append(f"{medium_severity_count} warning(s)")
    if low_severity_count:
        parts.append(f"{low_severity_count} suggestion(s)")

    return "⚠ " + ", ".join(parts)


def batch_validate_metadata(
    metadata_list: List[Dict[str, str]], metadata_type: str
) -> List[Dict[str, any]]:
    """
    Validate multiple metadata entries at once.

    Args:
        metadata_list: List of dicts with {"page_id": str, "value": str}
        metadata_type: Either "title" or "description"

    Returns:
        List of validation results with page_id included
    """
    results = []

    for item in metadata_list:
        page_id = item.get("page_id")
        value = item.get("value", "")

        if metadata_type == "title":
            validation = validate_title(value)
        elif metadata_type == "description":
            validation = validate_meta_description(value)
        else:
            validation = {
                "is_valid": False,
                "issues": [
                    {
                        "type": "invalid_type",
                        "severity": "high",
                        "message": "Invalid metadata type",
                    }
                ],
            }

        results.append({"page_id": page_id, **validation})

    return results
