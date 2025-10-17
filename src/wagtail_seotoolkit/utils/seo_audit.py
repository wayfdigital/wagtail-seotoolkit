"""
SEO Audit utilities for analyzing HTML pages and detecting SEO issues.

This module provides the main SEOAuditor class that orchestrates various SEO checks
using modular checker classes.
"""
from typing import Any, Dict, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from tqdm import tqdm

from wagtail_seotoolkit.models import SEOAuditIssueSeverity
from wagtail_seotoolkit.utils.checkers import (
    ContentChecker,
    FreshnessChecker,
    HeaderChecker,
    ImageChecker,
    LinkChecker,
    MetaChecker,
    MobileChecker,
    SchemaChecker,
    TitleChecker,
)

# ==================== Constants ====================

# Scoring
SCORE_PENALTY_PER_ISSUE = 5


# ==================== Helper Functions ====================


def extract_base_domain(url: str) -> str:
    """Extract base domain from a URL."""
    if not url:
        return ""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


# ==================== SEO Auditor Class ====================


class SEOAuditor:
    """Main SEO auditor class that runs all checks on HTML content."""

    def __init__(
        self,
        html: str,
        url: str = "",
        base_domain: str = "",
    ):
        """
        Initialize the auditor with HTML content.

        Args:
            html: The HTML content to audit
            url: The URL of the page being audited
            base_domain: The base domain to identify internal links
        """
        self.html = html
        self.url = url
        self.base_domain = base_domain or extract_base_domain(url)
        self.soup = BeautifulSoup(html, "html.parser")
        self.issues: List[Dict[str, Any]] = []

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Run all SEO checks and return a list of issues."""
        self.issues = []

        # Initialize all checkers
        checkers = [
            TitleChecker(self.soup, self.url, self.base_domain),
            MetaChecker(self.soup, self.url, self.base_domain),
            ContentChecker(self.soup, self.url, self.base_domain),
            HeaderChecker(self.soup, self.url, self.base_domain),
            ImageChecker(self.soup, self.url, self.base_domain),
            SchemaChecker(self.soup, self.url, self.base_domain),
            MobileChecker(self.soup, self.url, self.base_domain),
            LinkChecker(self.soup, self.url, self.base_domain),
            FreshnessChecker(self.soup, self.url, self.base_domain),
        ]

        # Run all checkers
        for checker in checkers:
            issues = checker.check()
            self.issues.extend(issues)

        return self.issues

    # Backward compatibility methods - delegate to checkers
    def check_title_tag(self) -> None:
        """Check for title tag issues. [DEPRECATED - Use run_all_checks()]"""
        checker = TitleChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_meta_description(self) -> None:
        """Check for meta description issues. [DEPRECATED - Use run_all_checks()]"""
        checker = MetaChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_content_depth(self) -> None:
        """Check for content depth issues. [DEPRECATED - Use run_all_checks()]"""
        checker = ContentChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_header_structure(self) -> None:
        """Check for header structure issues. [DEPRECATED - Use run_all_checks()]"""
        checker = HeaderChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_image_alt_text(self) -> None:
        """Check for image alt text issues. [DEPRECATED - Use run_all_checks()]"""
        checker = ImageChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_structured_data(self) -> None:
        """Check for structured data issues. [DEPRECATED - Use run_all_checks()]"""
        checker = SchemaChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_mobile_responsiveness(self) -> None:
        """Check for mobile responsiveness issues. [DEPRECATED - Use run_all_checks()]"""
        checker = MobileChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_internal_linking(self) -> None:
        """Check for internal linking issues. [DEPRECATED - Use run_all_checks()]"""
        checker = LinkChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())

    def check_content_freshness(self) -> None:
        """Check for content freshness issues. [DEPRECATED - Use run_all_checks()]"""
        checker = FreshnessChecker(self.soup, self.url, self.base_domain)
        self.issues.extend(checker.check())


# ==================== Page Rendering ====================


def get_page_html(page) -> str:
    """
    Get HTML content for a Wagtail page.

    Attempts to render the page using Wagtail's render method.

    Args:
        page: The Wagtail page to get HTML from

    Returns:
        HTML string
    """
    try:
        # Get the rendered content from the page
        request = HttpRequest()
        # Add necessary attributes to the request
        site = page.get_site()
        request.META = {"SERVER_NAME": site.hostname, "SERVER_PORT": site.port}
        request.path = page.url
        request.user = AnonymousUser()
        rendered_content = page.serve(request).render()
        if isinstance(rendered_content.content, bytes):
            return rendered_content.content.decode("utf-8")
        else:
            return str(rendered_content.content)
    except Exception as e:
        # Use tqdm.write to avoid breaking the progress bar
        tqdm.write(f"  ⚠️  Could not render {page.title}: {e}")


# ==================== Audit Execution ====================


def audit_single_page(page, audit_run) -> List[Dict[str, Any]]:
    """
    Audit a single Wagtail page and create issue records.

    Args:
        page: The Wagtail page to audit
        audit_run: The SEOAuditRun instance to attach issues to

    Returns:
        List of issues found
    """
    from wagtail_seotoolkit.models import SEOAuditIssue

    # Get HTML content
    html = get_page_html(page)

    # Get page URL and base domain
    url = page.get_full_url() if hasattr(page, "get_full_url") else page.url
    base_domain = extract_base_domain(url)

    # Run audit
    auditor = SEOAuditor(html, url=url, base_domain=base_domain)
    issues = auditor.run_all_checks()

    # Create issue records
    for issue_data in issues:
        SEOAuditIssue.objects.create(
            audit_run=audit_run,
            page=page,  # Link to the actual page object
            issue_type=issue_data["issue_type"],
            issue_severity=issue_data["issue_severity"],
            page_url=issue_data.get("page_url", ""),
            page_title=page.title,
            description=issue_data["description"],
        )

    return issues


def run_audit_on_pages(
    pages: List, audit_run, show_progress: bool = True
) -> Dict[str, Any]:
    """
    Run SEO audit on a list of Wagtail pages.

    Args:
        pages: List of Wagtail pages to audit
        audit_run: The SEOAuditRun instance to attach issues to
        show_progress: Whether to show a progress bar

    Returns:
        Dictionary with audit results summary
    """
    total_pages = len(pages)
    total_issues = 0

    # Audit each page
    if show_progress:
        total_issues = _audit_with_progress(pages, audit_run)
    else:
        for page in pages:
            issues = audit_single_page(page, audit_run)
            total_issues += len(issues)

    # Calculate and save results
    overall_score = calculate_audit_score(total_issues, total_pages)
    audit_run.status = "completed"
    audit_run.overall_score = overall_score
    audit_run.pages_analyzed = total_pages
    audit_run.save()

    # Get breakdown by severity
    return {
        "total_pages": total_pages,
        "total_issues": total_issues,
        "overall_score": overall_score,
        "high_issues": audit_run.issues.filter(
            issue_severity=SEOAuditIssueSeverity.HIGH
        ).count(),
        "medium_issues": audit_run.issues.filter(
            issue_severity=SEOAuditIssueSeverity.MEDIUM
        ).count(),
        "low_issues": audit_run.issues.filter(
            issue_severity=SEOAuditIssueSeverity.LOW
        ).count(),
    }


def _audit_with_progress(pages: List, audit_run) -> int:
    """Audit pages with a progress bar."""
    total_issues = 0

    with tqdm(total=len(pages), desc="Auditing pages", unit="page") as pbar:
        for page in pages:
            pbar.set_description(f"Auditing: {page.title[:50]}")

            issues = audit_single_page(page, audit_run)
            total_issues += len(issues)

            pbar.set_postfix({"issues": total_issues})
            pbar.update(1)

    return total_issues


def calculate_audit_score(total_issues: int, total_pages: int) -> int:
    """
    Calculate an overall SEO score based on issues found.

    Score calculation:
    - 0 issues = 100
    - 1 issue per page = 95
    - 5 issues per page = 75
    - 10 issues per page = 50
    - 20+ issues per page = 0

    Args:
        total_issues: Total number of issues found
        total_pages: Total number of pages audited

    Returns:
        Score from 0-100
    """
    if total_pages == 0:
        return 100

    avg_issues = total_issues / total_pages
    score = max(0, 100 - (avg_issues * SCORE_PENALTY_PER_ISSUE))

    return int(score)


def execute_audit_run(audit_run, pages=None, show_progress=True):
    """
    Execute an audit run on the provided pages.

    This is the core audit execution function that can be called by both
    the CLI command and the scheduled audit command.

    Args:
        audit_run: The SEOAuditRun instance to execute
        pages: List of pages to audit (if None, will audit all live pages)
        show_progress: Whether to show progress bar (default: True)

    Returns:
        Dictionary with audit results summary
    """
    from wagtail.models import Page

    # Get pages to audit if not provided
    if pages is None:
        pages = Page.objects.live().public().specific()
        # Exclude root and system pages
        pages = pages.exclude(depth__lte=2)
        pages = list(pages)

    # Update audit run status to running
    audit_run.status = "running"
    audit_run.save()

    try:
        # Run the audit
        results = run_audit_on_pages(pages, audit_run, show_progress=show_progress)
        return results

    except Exception as e:
        # Mark audit as failed
        audit_run.status = "failed"
        audit_run.save()
        raise e
