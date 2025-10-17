"""
Base checker class for SEO auditing.

All checker classes should inherit from BaseChecker to ensure consistent interface.
"""
from typing import Any, Dict, List

from bs4 import BeautifulSoup


class BaseChecker:
    """Base class for all SEO checkers."""

    def __init__(self, soup: BeautifulSoup, url: str = "", base_domain: str = ""):
        """
        Initialize the checker.

        Args:
            soup: BeautifulSoup instance of the HTML
            url: The URL of the page being audited
            base_domain: The base domain to identify internal links
        """
        self.soup = soup
        self.url = url
        self.base_domain = base_domain
        self.issues: List[Dict[str, Any]] = []

    def add_issue(self, issue_type: str, severity: str, description: str) -> None:
        """
        Add an issue to the issues list.

        Args:
            issue_type: Type of the SEO issue
            severity: Severity level of the issue
            description: Detailed description of the issue
        """
        self.issues.append({
            "issue_type": issue_type,
            "issue_severity": severity,
            "description": description,
            "page_url": self.url,
        })

    def check(self) -> List[Dict[str, Any]]:
        """
        Run all checks for this checker.

        Returns:
            List of issues found

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement check() method")

