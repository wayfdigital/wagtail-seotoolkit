"""
Header structure checker.

Checks for H1 presence, header hierarchy, and subheading usage.
"""
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker

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


class HeaderChecker(BaseChecker):
    """Checker for header structure."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for header structure issues."""
        self.issues = []

        h1_tags = self.soup.find_all("h1")

        if len(h1_tags) == 0:
            self.add_issue(
                SEOAuditIssueType.HEADER_NO_H1,
                SEOAuditIssueSeverity.HIGH,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.HEADER_NO_H1
                ),
            )
        elif len(h1_tags) > 1:
            self.add_issue(
                SEOAuditIssueType.HEADER_MULTIPLE_H1,
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.HEADER_MULTIPLE_H1
                ).format(count=len(h1_tags)),
            )

        # Check for subheadings on content pages
        if is_content_page(self.soup):
            h2_tags = self.soup.find_all("h2")
            h3_tags = self.soup.find_all("h3")

            if len(h2_tags) == 0 and len(h3_tags) == 0:
                body = self.soup.find("body")
                word_count = (
                    count_words(body.get_text(separator=" ", strip=True))
                    if body
                    else 0
                )
                self.add_issue(
                    SEOAuditIssueType.HEADER_NO_SUBHEADINGS,
                    SEOAuditIssueSeverity.MEDIUM,
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.HEADER_NO_SUBHEADINGS
                    ).format(word_count=word_count),
                )

        # Check header hierarchy
        self._check_header_hierarchy()

        return self.issues

    def _check_header_hierarchy(self) -> None:
        """Check if header hierarchy is properly maintained."""
        headers = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if len(headers) <= 1:
            return

        prev_level = 0
        for header in headers:
            current_level = int(header.name[1])
            if prev_level > 0 and current_level > prev_level + 1:
                self.add_issue(
                    SEOAuditIssueType.HEADER_BROKEN_HIERARCHY,
                    SEOAuditIssueSeverity.LOW,
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.HEADER_BROKEN_HIERARCHY
                    ).format(current=header.name.upper(), previous=f"H{prev_level}"),
                )
                break
            prev_level = current_level

