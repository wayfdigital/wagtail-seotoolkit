"""
JSON-LD Schema Validator for Rich Results Eligibility.

This module provides functions to extract, parse, and validate JSON-LD structured data
against Google's rich results requirements.

Uses the rules defined in rich_results_rules.py for validation.
"""

import json
from typing import Any, Dict, List, Optional, Set

from bs4 import BeautifulSoup

from wagtail_seotoolkit.core.utils.rich_results_rules import (
    BASIC_SCHEMA_TYPES,
    DEPRECATED_TYPES,
    RICH_RESULTS_RULES,
    get_deprecation_info,
    get_rules_for_type,
    is_basic_type,
    is_deprecated_type,
    is_rich_result_type,
)


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """
    Extract and parse all JSON-LD blocks from HTML.

    Args:
        html: The HTML content to parse

    Returns:
        List of parsed JSON-LD objects (may contain nested @graph items)
    """
    soup = BeautifulSoup(html, "html.parser")
    json_ld_scripts = soup.find_all("script", type="application/ld+json")

    schemas = []
    for script in json_ld_scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                schemas.append(data)
        except json.JSONDecodeError:
            # Will be captured as syntax error
            continue

    return schemas


def normalize_schemas(schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize JSON-LD schemas by flattening @graph arrays.

    Args:
        schemas: List of raw JSON-LD objects

    Returns:
        Flattened list of individual schema objects
    """
    normalized = []

    for schema in schemas:
        if isinstance(schema, list):
            # Handle arrays of schemas
            normalized.extend(schema)
        elif isinstance(schema, dict):
            # Handle @graph arrays
            if "@graph" in schema:
                graph = schema["@graph"]
                if isinstance(graph, list):
                    normalized.extend(graph)
                else:
                    normalized.append(graph)
            else:
                normalized.append(schema)

    return normalized


def get_schema_type(schema: Dict[str, Any]) -> Optional[str]:
    """
    Get the @type from a schema object.

    Args:
        schema: A JSON-LD schema object

    Returns:
        The type string, or None if not found
    """
    schema_type = schema.get("@type")

    if isinstance(schema_type, list):
        # Return first type if array
        return schema_type[0] if schema_type else None
    return schema_type


def validate_required_properties(
    schema: Dict[str, Any], required: List[str]
) -> List[str]:
    """
    Check which required properties are missing from a schema.

    Args:
        schema: The schema object to validate
        required: List of required property names

    Returns:
        List of missing property names
    """
    missing = []
    for prop in required:
        if prop not in schema or schema[prop] is None:
            missing.append(prop)
        elif isinstance(schema[prop], str) and not schema[prop].strip():
            missing.append(prop)
    return missing


def validate_nested_properties(
    schema: Dict[str, Any], nested_rules: Dict[str, Any]
) -> List[str]:
    """
    Validate nested properties according to rules.

    Args:
        schema: The schema object to validate
        nested_rules: Rules for nested properties

    Returns:
        List of missing property paths (e.g., "offers.price")
    """
    missing = []

    for prop_name, rules in nested_rules.items():
        prop_value = schema.get(prop_name)

        if prop_value is None:
            continue  # Parent property not present, not a nested issue

        # Handle array properties (like mainEntity in FAQPage)
        if isinstance(prop_value, list):
            for idx, item in enumerate(prop_value):
                if isinstance(item, dict):
                    # Check required properties for each item
                    if "required" in rules:
                        for req_prop in rules["required"]:
                            if req_prop not in item or item[req_prop] is None:
                                missing.append(f"{prop_name}[{idx}].{req_prop}")

                    # Check nested rules recursively
                    if "nested_rules" in rules:
                        nested_missing = validate_nested_properties(
                            item, rules["nested_rules"]
                        )
                        missing.extend(
                            [f"{prop_name}[{idx}].{m}" for m in nested_missing]
                        )

        elif isinstance(prop_value, dict):
            # Check required properties for single object
            if "required" in rules:
                for req_prop in rules["required"]:
                    if req_prop not in prop_value or prop_value[req_prop] is None:
                        missing.append(f"{prop_name}.{req_prop}")

            # Check nested rules recursively
            if "nested_rules" in rules:
                nested_missing = validate_nested_properties(
                    prop_value, rules["nested_rules"]
                )
                missing.extend([f"{prop_name}.{m}" for m in nested_missing])

    return missing


def get_missing_recommended(
    schema: Dict[str, Any], recommended: List[str]
) -> List[str]:
    """
    Check which recommended properties are missing from a schema.

    Args:
        schema: The schema object to validate
        recommended: List of recommended property names

    Returns:
        List of missing recommended property names
    """
    missing = []
    for prop in recommended:
        if prop not in schema or schema[prop] is None:
            missing.append(prop)
    return missing


def validate_single_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single schema object against rich results rules.

    Args:
        schema: A JSON-LD schema object

    Returns:
        Validation result dictionary
    """
    schema_type = get_schema_type(schema)

    if not schema_type:
        return {
            "type": "Unknown",
            "eligible": False,
            "status": "invalid",
            "missing_required": [],
            "missing_recommended": [],
            "error": "No @type specified",
        }

    # Check if deprecated
    if is_deprecated_type(schema_type):
        deprecation_info = get_deprecation_info(schema_type)
        return {
            "type": schema_type,
            "eligible": False,
            "status": "deprecated",
            "missing_required": [],
            "missing_recommended": [],
            "note": deprecation_info.get("note", "This type is deprecated"),
            "deprecated_date": deprecation_info.get("deprecated_date"),
        }

    # Check if basic type (informational only)
    if is_basic_type(schema_type):
        return {
            "type": schema_type,
            "eligible": False,
            "status": "basic",
            "missing_required": [],
            "missing_recommended": [],
            "note": "Basic schema type - not eligible for rich results but valid",
        }

    # Get rules for this type
    rules = get_rules_for_type(schema_type)

    if not rules:
        # Unknown type - not recognized as rich result eligible
        return {
            "type": schema_type,
            "eligible": False,
            "status": "unknown",
            "missing_required": [],
            "missing_recommended": [],
            "note": "Not recognized as a rich result type",
        }

    # Validate required properties
    missing_required = validate_required_properties(
        schema, rules.get("required", [])
    )

    # Validate nested required properties
    if "nested_rules" in rules:
        nested_missing = validate_nested_properties(schema, rules["nested_rules"])
        missing_required.extend(nested_missing)

    # Get missing recommended
    missing_recommended = get_missing_recommended(
        schema, rules.get("recommended", [])
    )

    # Determine eligibility
    eligible = len(missing_required) == 0

    # Determine status
    if eligible:
        status = "valid"
    else:
        status = "missing_required"

    result = {
        "type": schema_type,
        "eligible": eligible,
        "status": status,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "description": rules.get("description", ""),
    }

    # Add note if present in rules
    if "note" in rules:
        result["note"] = rules["note"]

    return result


def check_syntax_errors(html: str) -> List[str]:
    """
    Check for JSON-LD syntax errors in HTML.

    Args:
        html: The HTML content to check

    Returns:
        List of syntax error messages
    """
    soup = BeautifulSoup(html, "html.parser")
    json_ld_scripts = soup.find_all("script", type="application/ld+json")

    errors = []
    for idx, script in enumerate(json_ld_scripts):
        try:
            if script.string:
                json.loads(script.string)
        except json.JSONDecodeError as e:
            errors.append(f"JSON-LD block {idx + 1}: {str(e)}")

    return errors


def get_schema_validation_details(html: str) -> Dict[str, Any]:
    """
    Get comprehensive schema validation details from HTML.

    This is the main entry point for schema validation.

    Args:
        html: The HTML content to validate

    Returns:
        Dictionary with validation details for UI display:
        {
            "has_schema": bool,
            "schemas": [
                {
                    "type": str,
                    "eligible": bool,
                    "status": str,  # valid, missing_required, deprecated, basic, unknown
                    "missing_required": [...],
                    "missing_recommended": [...],
                    "description": str,
                    "note": str (optional),
                }
            ],
            "basic_types": [str],  # Types that are valid but not rich-result eligible
            "syntax_errors": [str],
            "total_schemas": int,
            "eligible_count": int,
            "has_issues": bool,  # True if any schema has issues
        }
    """
    # Check for syntax errors first
    syntax_errors = check_syntax_errors(html)

    # Extract and normalize schemas
    raw_schemas = extract_json_ld(html)
    schemas = normalize_schemas(raw_schemas)

    if not schemas and not syntax_errors:
        return {
            "has_schema": False,
            "schemas": [],
            "basic_types": [],
            "syntax_errors": [],
            "total_schemas": 0,
            "eligible_count": 0,
            "has_issues": True,  # No schema is an issue
        }

    # Validate each schema
    validation_results = []
    basic_types: Set[str] = set()
    eligible_count = 0
    has_issues = len(syntax_errors) > 0

    for schema in schemas:
        if not isinstance(schema, dict):
            continue

        result = validate_single_schema(schema)

        # Track basic types separately
        if result["status"] == "basic":
            basic_types.add(result["type"])
            continue

        validation_results.append(result)

        if result["eligible"]:
            eligible_count += 1
        else:
            has_issues = True

    # Also mark as having issues if there are missing recommended properties
    # but only if there are eligible schemas (don't double-count)
    for result in validation_results:
        if result.get("missing_recommended"):
            # This is a soft issue, not a hard failure
            pass

    return {
        "has_schema": len(schemas) > 0 or len(syntax_errors) > 0,
        "schemas": validation_results,
        "basic_types": sorted(list(basic_types)),
        "syntax_errors": syntax_errors,
        "total_schemas": len(validation_results),
        "eligible_count": eligible_count,
        "has_issues": has_issues,
    }
