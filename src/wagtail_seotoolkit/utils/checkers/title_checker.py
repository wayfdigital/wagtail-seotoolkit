"""
Title tag optimization checker.

Checks for title tag presence, length, and SEO best practices.
"""
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueType

from .base import BaseChecker

# Title tag constraints
TITLE_MIN_LENGTH = 50
TITLE_MAX_LENGTH = 60


class TitleChecker(BaseChecker):
    """Checker for title tag optimization."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for title tag issues."""
        self.issues = []

        title_tag = self.soup.find("title")

        if not title_tag or not title_tag.string:
            self.add_issue(
                SEOAuditIssueType.TITLE_MISSING,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.TITLE_MISSING),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_MISSING
                ),
            )
            return self.issues

        title_text = title_tag.string.strip()
        title_length = len(title_text)

        if title_length < TITLE_MIN_LENGTH:
            self.add_issue(
                SEOAuditIssueType.TITLE_TOO_SHORT,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.TITLE_TOO_SHORT),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_TOO_SHORT
                ).format(
                    length=title_length,
                    min_length=TITLE_MIN_LENGTH,
                    max_length=TITLE_MAX_LENGTH,
                    title=title_text,
                ),
            )
        elif title_length > TITLE_MAX_LENGTH:
            self.add_issue(
                SEOAuditIssueType.TITLE_TOO_LONG,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.TITLE_TOO_LONG),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.TITLE_TOO_LONG
                ).format(
                    length=title_length,
                    min_length=TITLE_MIN_LENGTH,
                    max_length=TITLE_MAX_LENGTH,
                ),
            )

        return self.issues

