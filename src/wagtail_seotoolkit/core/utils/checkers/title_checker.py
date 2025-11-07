"""
Title tag optimization checker.

Checks for title tag presence, length, and SEO best practices.
"""

from typing import Any, Dict, List

from wagtail_seotoolkit.core.models import SEOAuditIssueType
from wagtail_seotoolkit.core.utils.seo_validators import (
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    validate_title,
)

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker


class TitleChecker(BaseChecker):
    """Checker for title tag optimization."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for title tag issues."""
        self.issues = []

        title_tag = self.soup.find("title")
        title_text = title_tag.string if title_tag and title_tag.string else ""

        # Use the reusable validation function
        validation_result = validate_title(title_text)

        # Convert validation results to audit issues
        for issue in validation_result["issues"]:
            issue_type = None
            description = issue["message"]

            if issue["type"] == "missing":
                issue_type = SEOAuditIssueType.TITLE_MISSING
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_MISSING
                )
            elif issue["type"] == "too_short":
                issue_type = SEOAuditIssueType.TITLE_TOO_SHORT
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_TOO_SHORT
                ).format(
                    length=validation_result["length"],
                    min_length=TITLE_MIN_LENGTH,
                    max_length=TITLE_MAX_LENGTH,
                    title=title_text.strip(),
                )
            elif issue["type"] == "too_long":
                issue_type = SEOAuditIssueType.TITLE_TOO_LONG
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_TOO_LONG
                ).format(
                    length=validation_result["length"],
                    min_length=TITLE_MIN_LENGTH,
                    max_length=TITLE_MAX_LENGTH,
                )

            if issue_type:
                self.add_issue(
                    issue_type,
                    SEOAuditIssueType.get_severity(issue_type),
                    description,
                )

        return self.issues
