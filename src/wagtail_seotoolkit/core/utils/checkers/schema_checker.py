"""
Structured data presence checker.

Checks for JSON-LD schema markup, validates schema types, and checks
rich results eligibility against Google's requirements.
"""

import json
from typing import Any, Dict, List

from wagtail_seotoolkit.core.models import SEOAuditIssueType

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker
from wagtail_seotoolkit.core.utils.schema_validator import (
    extract_json_ld,
    get_schema_validation_details,
    normalize_schemas,
)

# Schema types
ORGANIZATION_SCHEMA_TYPES = {"Organization", "Person", "LocalBusiness"}
ARTICLE_SCHEMA_TYPES = {"Article", "BlogPosting", "NewsArticle", "ScholarlyArticle"}

# Content constraints
MIN_WORD_COUNT = 300


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def is_content_page(soup, min_words: int = MIN_WORD_COUNT) -> bool:
    """Check if page is a content page based on word count."""
    body = soup.find("body")
    if not body:
        return False
    text_content = body.get_text(separator=" ", strip=True)
    return count_words(text_content) > min_words


class SchemaChecker(BaseChecker):
    """Checker for structured data presence and rich results eligibility."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for structured data issues and rich results eligibility."""
        self.issues = []

        json_ld_scripts = self.soup.find_all("script", type="application/ld+json")

        if len(json_ld_scripts) == 0:
            self.add_issue(
                SEOAuditIssueType.SCHEMA_MISSING,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.SCHEMA_MISSING),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.SCHEMA_MISSING
                ),
            )
            return self.issues

        schema_types = self._parse_schema_types(json_ld_scripts)

        # Check for Organization/Person
        if not schema_types.intersection(ORGANIZATION_SCHEMA_TYPES):
            self.add_issue(
                SEOAuditIssueType.SCHEMA_NO_ORGANIZATION,
                SEOAuditIssueType.get_severity(
                    SEOAuditIssueType.SCHEMA_NO_ORGANIZATION
                ),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.SCHEMA_NO_ORGANIZATION
                ),
            )

        # Check for Article/BlogPosting on content pages
        if is_content_page(self.soup) and not schema_types.intersection(
            ARTICLE_SCHEMA_TYPES
        ):
            self.add_issue(
                SEOAuditIssueType.SCHEMA_NO_ARTICLE,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.SCHEMA_NO_ARTICLE),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.SCHEMA_NO_ARTICLE
                ),
            )

        # Run rich results eligibility checks
        self._check_rich_results_eligibility()

        return self.issues

    def _check_rich_results_eligibility(self) -> None:
        """Check schemas for rich results eligibility issues."""
        # Get the HTML from the soup
        html = str(self.soup)
        validation_details = get_schema_validation_details(html)

        # Check for syntax errors
        for error in validation_details.get("syntax_errors", []):
            self.add_issue(
                SEOAuditIssueType.SCHEMA_INVALID,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.SCHEMA_INVALID),
                f"JSON-LD syntax error: {error}",
            )

        # Check each schema for eligibility issues
        for schema_result in validation_details.get("schemas", []):
            schema_type = schema_result.get("type", "Unknown")
            status = schema_result.get("status", "")

            # Check for deprecated types
            if status == "deprecated":
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.SCHEMA_RICH_RESULT_DEPRECATED
                ).format(
                    schema_type=schema_type,
                )
                if schema_result.get("note"):
                    description += f" Note: {schema_result['note']}"

                self.add_issue(
                    SEOAuditIssueType.SCHEMA_RICH_RESULT_DEPRECATED,
                    SEOAuditIssueType.get_severity(
                        SEOAuditIssueType.SCHEMA_RICH_RESULT_DEPRECATED
                    ),
                    description,
                )

            # Check for missing required properties
            elif status == "missing_required":
                missing_props = schema_result.get("missing_required", [])
                if missing_props:
                    description = SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.SCHEMA_RICH_RESULT_MISSING_REQUIRED
                    ).format(
                        schema_type=schema_type,
                        missing_props=", ".join(missing_props),
                    )

                    self.add_issue(
                        SEOAuditIssueType.SCHEMA_RICH_RESULT_MISSING_REQUIRED,
                        SEOAuditIssueType.get_severity(
                            SEOAuditIssueType.SCHEMA_RICH_RESULT_MISSING_REQUIRED
                        ),
                        description,
                    )

    def _parse_schema_types(self, json_ld_scripts) -> set:
        """Parse and validate JSON-LD scripts, returning schema types."""
        schema_types = set()

        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)

                # Handle both single objects and arrays
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]

                for item in schema_data:
                    if "@type" in item:
                        schema_type = item["@type"]
                        if isinstance(schema_type, list):
                            schema_types.update(schema_type)
                        else:
                            schema_types.add(schema_type)

                    # Also check @graph items
                    if "@graph" in item:
                        for graph_item in item.get("@graph", []):
                            if isinstance(graph_item, dict) and "@type" in graph_item:
                                graph_type = graph_item["@type"]
                                if isinstance(graph_type, list):
                                    schema_types.update(graph_type)
                                else:
                                    schema_types.add(graph_type)

            except (json.JSONDecodeError, AttributeError):
                self.add_issue(
                    SEOAuditIssueType.SCHEMA_INVALID,
                    SEOAuditIssueType.get_severity(SEOAuditIssueType.SCHEMA_INVALID),
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.SCHEMA_INVALID
                    ),
                )

        return schema_types
