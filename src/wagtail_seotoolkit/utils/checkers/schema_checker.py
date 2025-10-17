"""
Structured data presence checker.

Checks for JSON-LD schema markup and validates schema types.
"""
import json
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker

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
    """Checker for structured data presence."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for structured data issues."""
        self.issues = []

        json_ld_scripts = self.soup.find_all("script", type="application/ld+json")

        if len(json_ld_scripts) == 0:
            self.add_issue(
                SEOAuditIssueType.SCHEMA_MISSING,
                SEOAuditIssueSeverity.HIGH,
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
                SEOAuditIssueSeverity.MEDIUM,
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
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.SCHEMA_NO_ARTICLE
                ),
            )

        return self.issues

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
            except (json.JSONDecodeError, AttributeError):
                self.add_issue(
                    SEOAuditIssueType.SCHEMA_INVALID,
                    SEOAuditIssueSeverity.HIGH,
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.SCHEMA_INVALID
                    ),
                )

        return schema_types

