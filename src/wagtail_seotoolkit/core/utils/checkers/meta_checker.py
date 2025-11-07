"""
Meta description quality checker.

Checks for meta description presence, length, and CTA presence.
"""

from typing import Any, Dict, List

from wagtail_seotoolkit.core.models import SEOAuditIssueType
from wagtail_seotoolkit.core.utils.seo_validators import (
    CTA_KEYWORDS,
    META_DESC_MAX_LENGTH,
    META_DESC_MIN_LENGTH,
    validate_meta_description,
)

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker


class MetaChecker(BaseChecker):
    """Checker for meta description quality."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for meta description issues."""
        self.issues = []

        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        desc_text = meta_desc.get("content", "").strip() if meta_desc else ""

        # Use the reusable validation function
        validation_result = validate_meta_description(desc_text)

        # Convert validation results to audit issues
        for issue in validation_result["issues"]:
            issue_type = None
            description = issue["message"]

            if issue["type"] == "missing":
                issue_type = SEOAuditIssueType.META_DESCRIPTION_MISSING
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_MISSING
                )
            elif issue["type"] == "too_short":
                issue_type = SEOAuditIssueType.META_DESCRIPTION_TOO_SHORT
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_TOO_SHORT
                ).format(
                    length=validation_result["length"],
                    min_length=META_DESC_MIN_LENGTH,
                    max_length=META_DESC_MAX_LENGTH,
                )
            elif issue["type"] == "too_long":
                issue_type = SEOAuditIssueType.META_DESCRIPTION_TOO_LONG
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_TOO_LONG
                ).format(
                    length=validation_result["length"],
                    min_length=META_DESC_MIN_LENGTH,
                    max_length=META_DESC_MAX_LENGTH,
                )
            elif issue["type"] == "no_cta":
                issue_type = SEOAuditIssueType.META_DESCRIPTION_NO_CTA
                description = SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.META_DESCRIPTION_NO_CTA
                ).format(cta_examples=", ".join(CTA_KEYWORDS[:5]))

            if issue_type:
                self.add_issue(
                    issue_type,
                    SEOAuditIssueType.get_severity(issue_type),
                    description,
                )

        return self.issues
