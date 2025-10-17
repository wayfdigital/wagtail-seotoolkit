"""
Mobile responsiveness checker.

Checks for viewport meta tag and fixed-width layouts.
"""
import re
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker


class MobileChecker(BaseChecker):
    """Checker for mobile responsiveness."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for mobile responsiveness issues."""
        self.issues = []

        # Check for viewport meta tag
        viewport = self.soup.find("meta", attrs={"name": "viewport"})

        if not viewport:
            self.add_issue(
                SEOAuditIssueType.MOBILE_NO_VIEWPORT,
                SEOAuditIssueSeverity.HIGH,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.MOBILE_NO_VIEWPORT
                ),
            )

        # Check for fixed-width layouts
        self._check_fixed_width_layout()

        return self.issues

    def _check_fixed_width_layout(self) -> None:
        """Check if page uses fixed-width layout."""
        fixed_width_pattern = re.compile(r"width\s*:\s*\d+px")

        # Check body or main container with fixed width
        body_tag = self.soup.find("body")
        main_containers = self.soup.find_all(
            ["div", "main", "section"],
            id=re.compile(r"(container|wrapper|main)", re.I),
            limit=5,
        )

        for container in [body_tag] + main_containers:
            if container and container.get("style"):
                if fixed_width_pattern.search(container.get("style", "")):
                    self.add_issue(
                        SEOAuditIssueType.MOBILE_FIXED_WIDTH,
                        SEOAuditIssueSeverity.MEDIUM,
                        SEOAuditIssueType.get_description_template(
                            SEOAuditIssueType.MOBILE_FIXED_WIDTH
                        ),
                    )
                    break

