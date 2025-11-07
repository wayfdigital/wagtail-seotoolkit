"""
Internal linking checker.

Checks for internal link presence and internal vs external link balance.
"""

from typing import Any, Dict, List

from wagtail_seotoolkit.core.models import SEOAuditIssueType

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker

# Internal linking constraints
MIN_INTERNAL_LINKS = 3

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


class LinkChecker(BaseChecker):
    """Checker for internal linking."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for internal linking issues."""
        self.issues = []

        all_links = self.soup.find_all("a", href=True)

        if len(all_links) == 0:
            return self.issues  # No links at all - not necessarily an issue

        internal_links, external_links = self._categorize_links(all_links)

        # Check for no internal links
        if len(internal_links) == 0:
            if len(external_links) > 0:
                self.add_issue(
                    SEOAuditIssueType.INTERNAL_LINKS_ALL_EXTERNAL,
                    SEOAuditIssueType.get_severity(
                        SEOAuditIssueType.INTERNAL_LINKS_ALL_EXTERNAL
                    ),
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.INTERNAL_LINKS_ALL_EXTERNAL
                    ).format(external_count=len(external_links)),
                )
            else:
                self.add_issue(
                    SEOAuditIssueType.INTERNAL_LINKS_NONE,
                    SEOAuditIssueType.get_severity(
                        SEOAuditIssueType.INTERNAL_LINKS_NONE
                    ),
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.INTERNAL_LINKS_NONE
                    ),
                )
        elif len(internal_links) < MIN_INTERNAL_LINKS and is_content_page(self.soup):
            self.add_issue(
                SEOAuditIssueType.INTERNAL_LINKS_FEW,
                SEOAuditIssueType.get_severity(SEOAuditIssueType.INTERNAL_LINKS_FEW),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.INTERNAL_LINKS_FEW
                ).format(count=len(internal_links), min_links=MIN_INTERNAL_LINKS),
            )

        return self.issues

    def _categorize_links(self, links) -> tuple:
        """Categorize links into internal and external."""
        internal_links = []
        external_links = []

        for link in links:
            href = link.get("href", "").strip()

            # Skip empty, anchor, and javascript links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Determine if internal or external
            if href.startswith("/") or (self.base_domain and self.base_domain in href):
                internal_links.append(link)
            elif href.startswith("http"):
                external_links.append(link)
            else:
                # Relative link - consider internal
                internal_links.append(link)

        return internal_links, external_links
