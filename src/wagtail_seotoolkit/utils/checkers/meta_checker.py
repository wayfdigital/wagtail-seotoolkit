"""
Meta description quality checker.

Checks for meta description presence, length, and CTA presence.
"""
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker

# Meta description constraints
META_DESC_MIN_LENGTH = 120
META_DESC_MAX_LENGTH = 160
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


class MetaChecker(BaseChecker):
    """Checker for meta description quality."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for meta description issues."""
        self.issues = []

        meta_desc = self.soup.find("meta", attrs={"name": "description"})

        if not meta_desc or not meta_desc.get("content"):
            self.add_issue(
                SEOAuditIssueType.META_DESCRIPTION_MISSING,
                SEOAuditIssueSeverity.HIGH,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_MISSING
                ),
            )
            return self.issues

        desc_text = meta_desc.get("content", "").strip()
        desc_length = len(desc_text)

        if desc_length < META_DESC_MIN_LENGTH:
            self.add_issue(
                SEOAuditIssueType.META_DESCRIPTION_TOO_SHORT,
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_TOO_SHORT
                ).format(
                    length=desc_length,
                    min_length=META_DESC_MIN_LENGTH,
                    max_length=META_DESC_MAX_LENGTH,
                ),
            )
        elif desc_length > META_DESC_MAX_LENGTH:
            self.add_issue(
                SEOAuditIssueType.META_DESCRIPTION_TOO_LONG,
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_TOO_LONG
                ).format(
                    length=desc_length,
                    min_length=META_DESC_MIN_LENGTH,
                    max_length=META_DESC_MAX_LENGTH,
                ),
            )

        # Check for CTA words
        if not any(word in desc_text.lower() for word in CTA_KEYWORDS):
            self.add_issue(
                SEOAuditIssueType.META_DESCRIPTION_NO_CTA,
                SEOAuditIssueSeverity.LOW,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_NO_CTA
                ).format(cta_examples=", ".join(CTA_KEYWORDS[:5])),
            )

        return self.issues

