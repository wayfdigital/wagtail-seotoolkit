"""
Content depth analysis checker.

Checks for content word count, paragraph structure, and content quality.
"""
from typing import Any, Dict, List

from wagtail_seotoolkit.models import SEOAuditIssueSeverity, SEOAuditIssueType

from .base import BaseChecker

# Content constraints
MIN_WORD_COUNT = 300
MIN_WORDS_FOR_PARAGRAPHS = 100


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


class ContentChecker(BaseChecker):
    """Checker for content depth analysis."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for content depth issues."""
        self.issues = []

        # Get main content - try to find main, article, or body content
        main_content = (
            self.soup.find("main")
            or self.soup.find("article")
            or self.soup.find("body")
        )

        if not main_content:
            self.add_issue(
                SEOAuditIssueType.CONTENT_EMPTY,
                SEOAuditIssueSeverity.HIGH,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_EMPTY
                ).format(content_type="discernible"),
            )
            return self.issues

        # Remove non-content elements
        content_copy = main_content.__copy__()
        for element in content_copy.find_all(
            ["script", "style", "nav", "header", "footer"]
        ):
            element.decompose()

        # Get text content
        text_content = content_copy.get_text(separator=" ", strip=True)
        word_count = count_words(text_content)

        if word_count == 0:
            self.add_issue(
                SEOAuditIssueType.CONTENT_EMPTY,
                SEOAuditIssueSeverity.HIGH,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_EMPTY
                ).format(content_type="text"),
            )
            return self.issues

        if word_count < MIN_WORD_COUNT:
            self.add_issue(
                SEOAuditIssueType.CONTENT_THIN,
                SEOAuditIssueSeverity.MEDIUM,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_THIN
                ).format(word_count=word_count, min_words=MIN_WORD_COUNT),
            )

        # Check for paragraphs
        paragraphs = content_copy.find_all("p")
        if word_count > MIN_WORDS_FOR_PARAGRAPHS and len(paragraphs) == 0:
            self.add_issue(
                SEOAuditIssueType.CONTENT_NO_PARAGRAPHS,
                SEOAuditIssueSeverity.LOW,
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_NO_PARAGRAPHS
                ),
            )

        return self.issues

