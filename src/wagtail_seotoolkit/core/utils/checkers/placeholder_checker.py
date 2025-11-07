"""
Placeholder processing checker.

Checks for unprocessed placeholders in SEO metadata when middleware processing is disabled.
This checker is different from others as it checks database fields directly rather than HTML.
"""

import re
from typing import Any, Dict, List

from django.conf import settings

from wagtail_seotoolkit.core.models import SEOAuditIssueType


class PlaceholderChecker:
    """
    Checker for unprocessed placeholders in SEO metadata.
    
    Unlike other checkers, this one operates on page objects directly
    rather than analyzing HTML content.
    """

    def __init__(self, page):
        """
        Initialize the checker.

        Args:
            page: The Wagtail page object to check
        """
        self.page = page
        self.issues: List[Dict[str, Any]] = []
        self.placeholder_pattern = re.compile(r'\{[^}]+\}')

    def check(self) -> List[Dict[str, Any]]:
        """
        Check for unprocessed placeholders in page SEO metadata.
        
        Only performs check if WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS is False,
        as placeholders should be processed at runtime when it's True.

        Returns:
            List of issues found
        """
        self.issues = []

        # Only check if middleware processing is disabled
        process_placeholders_enabled = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS", True
        )

        if process_placeholders_enabled:
            # Middleware processing is enabled, placeholders are OK
            return self.issues

        found_placeholders = []

        # Check seo_title for placeholders
        if self.page.seo_title and self.placeholder_pattern.search(self.page.seo_title):
            placeholders = self.placeholder_pattern.findall(self.page.seo_title)
            found_placeholders.extend([f"seo_title: {p}" for p in placeholders])

        # Check search_description for placeholders
        if self.page.search_description and self.placeholder_pattern.search(
            self.page.search_description
        ):
            placeholders = self.placeholder_pattern.findall(self.page.search_description)
            found_placeholders.extend([f"search_description: {p}" for p in placeholders])

        # Create issue if placeholders were found
        if found_placeholders:
            placeholders_str = ", ".join(set(found_placeholders))
            description = SEOAuditIssueType.get_description_template(
                SEOAuditIssueType.PLACEHOLDER_UNPROCESSED
            ).format(placeholders=placeholders_str)

            self.issues.append(
                {
                    "issue_type": SEOAuditIssueType.PLACEHOLDER_UNPROCESSED,
                    "issue_severity": SEOAuditIssueType.get_severity(
                        SEOAuditIssueType.PLACEHOLDER_UNPROCESSED
                    ),
                    "description": description,
                    "page_url": self.page.get_full_url()
                    if hasattr(self.page, "get_full_url")
                    else self.page.url,
                }
            )

        return self.issues

