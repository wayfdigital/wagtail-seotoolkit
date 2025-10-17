"""
Image alt text checker.

Checks for missing, generic, or too-long alt text on images.
"""
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker

# Image alt text constraints
GENERIC_ALT_TEXTS = ["image", "photo", "picture", "img", "icon"]
MAX_ALT_LENGTH = 125


class ImageChecker(BaseChecker):
    """Checker for image alt text."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for image alt text issues."""
        self.issues = []

        images = self.soup.find_all("img")
        images_without_alt = 0

        for img in images:
            alt_text = img.get("alt", "").strip()

            if not alt_text:
                images_without_alt += 1
            else:
                # Check for generic alt
                if alt_text.lower() in GENERIC_ALT_TEXTS:
                    self.add_issue(
                        SEOAuditIssueType.IMAGE_ALT_GENERIC,
                        SEOAuditIssueSeverity.LOW,
                        SEOAuditIssueType.get_description_template(
                            SEOAuditIssueType.IMAGE_ALT_GENERIC
                        ).format(alt_text=alt_text),
                    )

                # Check for too long alt
                if len(alt_text) > MAX_ALT_LENGTH:
                    self.add_issue(
                        SEOAuditIssueType.IMAGE_ALT_TOO_LONG,
                        SEOAuditIssueSeverity.LOW,
                        SEOAuditIssueType.get_description_template(
                            SEOAuditIssueType.IMAGE_ALT_TOO_LONG
                        ).format(length=len(alt_text), max_length=MAX_ALT_LENGTH),
                    )

        if images_without_alt > 0:
            self.add_issue(
                SEOAuditIssueType.IMAGE_NO_ALT,
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.IMAGE_NO_ALT
                ).format(count=images_without_alt),
            )

        return self.issues

