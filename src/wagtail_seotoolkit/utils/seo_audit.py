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
    PageSpeedChecker,
    SchemaChecker,
    TitleChecker,
)

# ==================== Constants ====================

# Scoring - Weighted penalties by severity
SCORE_PENALTY_HIGH = 10    # Critical SEO issues (missing titles, H1, viewport)
SCORE_PENALTY_MEDIUM = 4   # Important issues (thin content, missing meta descriptions)
SCORE_PENALTY_LOW = 1      # Minor issues (generic alt text, no CTAs)


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
        debug: bool = False,
        skip_pagespeed: bool = False,
    ):
        """
        Initialize the auditor with HTML content.

        Args:
            html: The HTML content to audit
            url: The URL of the page being audited
            base_domain: The base domain to identify internal links
            debug: Enable debug output
            skip_pagespeed: Skip PageSpeed checks for this audit
        """
        self.html = html
        self.url = url
        self.base_domain = base_domain or extract_base_domain(url)
        self.soup = BeautifulSoup(html, "html.parser")
        self.issues: List[Dict[str, Any]] = []
        self.debug = debug
        self.skip_pagespeed = skip_pagespeed

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

        # Add PageSpeed checker if not skipped
        if not self.skip_pagespeed:
            checkers.append(
                PageSpeedChecker(
                    self.soup, self.url, self.base_domain, debug=self.debug
                )
            )

        # Run all checkers
        for checker in checkers:
            issues = checker.check()
            self.issues.extend(issues)

        # Filter out dev-fix issues if disabled in settings
        from django.conf import settings

        include_dev_fixes = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_INCLUDE_DEV_FIXES", True
        )

        if not include_dev_fixes:
            from wagtail_seotoolkit.models import SEOAuditIssueType

            original_count = len(self.issues)
            self.issues = [
                issue
                for issue in self.issues
                if not SEOAuditIssueType.requires_dev_fix(issue["issue_type"])
            ]
            if self.debug and len(self.issues) < original_count:
                filtered_count = original_count - len(self.issues)
                print(
                    f"[DEBUG] Filtered out {filtered_count} dev-fix issues globally (WAGTAIL_SEOTOOLKIT_INCLUDE_DEV_FIXES=False)"
                )

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


def audit_single_page(
    page, audit_run, debug=False, skip_pagespeed=False
) -> List[Dict[str, Any]]:
    """
    Audit a single Wagtail page and create issue records.

    Args:
        page: The Wagtail page to audit
        audit_run: The SEOAuditRun instance to attach issues to
        debug: Enable debug output
        skip_pagespeed: Skip PageSpeed checks for this audit

    Returns:
        List of issues found
    """
    from wagtail_seotoolkit.models import SEOAuditIssue, SEOAuditIssueType

    # Get HTML content
    html = get_page_html(page)

    # Get page URL and base domain
    url = page.get_full_url() if hasattr(page, "get_full_url") else page.url
    base_domain = extract_base_domain(url)

    # Run audit
    auditor = SEOAuditor(
        html,
        url=url,
        base_domain=base_domain,
        debug=debug,
        skip_pagespeed=skip_pagespeed,
    )
    issues = auditor.run_all_checks()

    # Create issue records
    for issue_data in issues:
        requires_dev_fix = SEOAuditIssueType.requires_dev_fix(issue_data["issue_type"])
        severity = SEOAuditIssueType.get_severity(issue_data["issue_type"])

        SEOAuditIssue.objects.create(
            audit_run=audit_run,
            page=page,  # Link to the actual page object
            issue_type=issue_data["issue_type"],
            issue_severity=severity,
            page_url=issue_data.get("page_url", ""),
            page_title=page.title,
            description=issue_data["description"],
            requires_dev_fix=requires_dev_fix,
        )

    return issues


def run_audit_on_pages(
    pages: List,
    audit_run,
    show_progress: bool = True,
    debug: bool = False,
    skip_pagespeed: bool = False,
) -> Dict[str, Any]:
    """
    Run SEO audit on a list of Wagtail pages.

    Args:
        pages: List of Wagtail pages to audit
        audit_run: The SEOAuditRun instance to attach issues to
        show_progress: Whether to show a progress bar
        debug: Enable debug output
        skip_pagespeed: Skip PageSpeed checks for this audit

    Returns:
        Dictionary with audit results summary
    """
    from django.conf import settings

    total_pages = len(pages)
    total_issues = 0

    # Check if dev fixes are disabled - if so, skip PageSpeed entirely
    include_dev_fixes = getattr(settings, "WAGTAIL_SEOTOOLKIT_INCLUDE_DEV_FIXES", True)
    if not include_dev_fixes:
        skip_pagespeed = True
        if debug:
            print("[DEBUG] Dev fixes disabled, skipping PageSpeed checks entirely")

    # Check if per-page-type optimization is enabled for PageSpeed only
    per_page_type = getattr(
        settings, "WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE", False
    )

    if per_page_type and not skip_pagespeed:
        # Run full SEO audits on all pages, but optimize PageSpeed checks per page type
        total_issues = _audit_with_pagespeed_per_page_type_optimization(
            pages, audit_run, show_progress, debug, skip_pagespeed
        )
    else:
        # Audit each page normally (all checkers run on every page)
        if show_progress:
            total_issues = _audit_with_progress(pages, audit_run, debug, skip_pagespeed)
        else:
            for page in pages:
                issues = audit_single_page(page, audit_run, debug, skip_pagespeed)
                total_issues += len(issues)

    # Get breakdown by severity
    high_issues = audit_run.issues.filter(
        issue_severity=SEOAuditIssueSeverity.HIGH
    ).count()
    medium_issues = audit_run.issues.filter(
        issue_severity=SEOAuditIssueSeverity.MEDIUM
    ).count()
    low_issues = audit_run.issues.filter(
        issue_severity=SEOAuditIssueSeverity.LOW
    ).count()

    # Calculate and save results using severity-weighted scoring
    overall_score = calculate_audit_score(high_issues, medium_issues, low_issues, total_pages)
    audit_run.status = "completed"
    audit_run.overall_score = overall_score
    audit_run.pages_analyzed = total_pages
    audit_run.save()

    return {
        "total_pages": total_pages,
        "total_issues": total_issues,
        "overall_score": overall_score,
        "high_issues": high_issues,
        "medium_issues": medium_issues,
        "low_issues": low_issues,
    }


def _audit_with_progress(
    pages: List, audit_run, debug: bool = False, skip_pagespeed: bool = False
) -> int:
    """Audit pages with a progress bar."""
    total_issues = 0

    with tqdm(total=len(pages), desc="Auditing pages", unit="page") as pbar:
        for page in pages:
            pbar.set_description(f"Auditing: {page.title[:50]}")

            issues = audit_single_page(page, audit_run, debug, skip_pagespeed)
            total_issues += len(issues)

            pbar.set_postfix({"issues": total_issues})
            pbar.update(1)

    return total_issues


def _audit_with_pagespeed_per_page_type_optimization(
    pages: List,
    audit_run,
    show_progress: bool = True,
    debug: bool = False,
    skip_pagespeed: bool = False,
) -> int:
    """
    Audit pages with PageSpeed per-page-type optimization.

    Completely separates PageSpeed testing from regular SEO testing:
    1. Test PageSpeed on one page per type (collect issues only)
    2. Run regular SEO audits on ALL pages (no PageSpeed)
    3. Propagate PageSpeed issues to remaining pages
    """
    from collections import defaultdict

    from wagtail_seotoolkit.models import SEOAuditIssue, SEOAuditIssueType

    total_issues = 0
    pagespeed_issues_by_type = {}  # Store PageSpeed issues for each page type
    pages_by_type = defaultdict(list)

    # Group pages by type
    for page in pages:
        page_type = page.specific_class.__name__
        pages_by_type[page_type].append(page)

    if debug:
        print(
            f"[DEBUG] Found {len(pages_by_type)} page types: {list(pages_by_type.keys())}"
        )

    # PHASE 1: Test PageSpeed on one page per type (collect issues only, don't create records)
    if show_progress:
        with tqdm(
            total=len(pages_by_type),
            desc="Testing PageSpeed per page type",
            unit="type",
        ) as pbar:
            for page_type, type_pages in pages_by_type.items():
                test_page = type_pages[0]  # Use first page of this type
                pbar.set_description(f"PageSpeed: {page_type}")

                if debug:
                    print(
                        f"[DEBUG] Testing PageSpeed for page type '{page_type}' using page: {test_page.title}"
                    )

                # Run PageSpeed check only (no regular SEO checks)
                pagespeed_issues = _run_pagespeed_only_check(test_page, debug)
                pagespeed_issues_by_type[page_type] = pagespeed_issues

                if debug and pagespeed_issues:
                    print(
                        f"[DEBUG] Found {len(pagespeed_issues)} PageSpeed issues for type '{page_type}'"
                    )

                pbar.update(1)
    else:
        for page_type, type_pages in pages_by_type.items():
            test_page = type_pages[0]  # Use first page of this type

            if debug:
                print(
                    f"[DEBUG] Testing PageSpeed for page type '{page_type}' using page: {test_page.title}"
                )

            # Run PageSpeed check only (no regular SEO checks)
            pagespeed_issues = _run_pagespeed_only_check(test_page, debug)
            pagespeed_issues_by_type[page_type] = pagespeed_issues

            if debug and pagespeed_issues:
                print(
                    f"[DEBUG] Found {len(pagespeed_issues)} PageSpeed issues for type '{page_type}'"
                )

    # PHASE 2: Run regular SEO audits on ALL pages (no PageSpeed)
    if show_progress:
        with tqdm(total=len(pages), desc="Auditing pages", unit="page") as pbar:
            for page in pages:
                pbar.set_description(f"Auditing: {page.title[:50]}")

                # Run regular SEO audit (no PageSpeed)
                issues = audit_single_page(page, audit_run, debug, skip_pagespeed=True)
                total_issues += len(issues)

                pbar.set_postfix({"issues": total_issues})
                pbar.update(1)
    else:
        for page in pages:
            # Run regular SEO audit (no PageSpeed)
            issues = audit_single_page(page, audit_run, debug, skip_pagespeed=True)
            total_issues += len(issues)

    # PHASE 3: Create PageSpeed issues for all pages of each type
    for page_type, type_pages in pages_by_type.items():
        if page_type in pagespeed_issues_by_type:
            pagespeed_issues = pagespeed_issues_by_type[page_type]

            if debug and pagespeed_issues:
                print(
                    f"[DEBUG] Creating {len(pagespeed_issues)} PageSpeed issues for {len(type_pages)} pages of type '{page_type}'"
                )

            # Create PageSpeed issues for ALL pages of this type
            for page in type_pages:
                for issue_data in pagespeed_issues:
                    requires_dev_fix = SEOAuditIssueType.requires_dev_fix(
                        issue_data["issue_type"]
                    )
                    severity = SEOAuditIssueType.get_severity(issue_data["issue_type"])

                    # Update description to indicate this affects all pages of this type
                    description = issue_data["description"]
                    if "affects all" not in description.lower():
                        description += f" (affects all {len(type_pages)} pages of type '{page_type}')"

                    SEOAuditIssue.objects.create(
                        audit_run=audit_run,
                        page=page,
                        issue_type=issue_data["issue_type"],
                        issue_severity=severity,
                        page_url=issue_data.get("page_url", ""),
                        page_title=page.title,
                        description=description,
                        requires_dev_fix=requires_dev_fix,
                    )
                    total_issues += 1

    return total_issues


def _run_pagespeed_only_check(page, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Run only PageSpeed check on a page (no regular SEO checks).
    Returns PageSpeed issues without creating database records.
    """
    from django.conf import settings
    from django.test import RequestFactory

    from wagtail_seotoolkit.utils.checkers.pagespeed_checker import PageSpeedChecker

    # Get page URL and HTML (same approach as audit_single_page)
    url = page.get_full_url()

    # Create a mock request for page.serve()
    factory = RequestFactory()
    request = factory.get(url, headers={"Host": settings.ALLOWED_HOSTS[0]})

    # Add a mock user to the request (some pages might need it)
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()

    # Render the response properly
    response = page.serve(request)
    response.render()
    html = response.content.decode("utf-8")

    # Run only PageSpeed check
    pagespeed_checker = PageSpeedChecker(html, url, "", debug=debug)
    pagespeed_issues = pagespeed_checker.check()

    # Filter to only PageSpeed issues
    pagespeed_issues = [
        issue
        for issue in pagespeed_issues
        if "pagespeed" in issue.get("issue_type", "").lower()
    ]

    return pagespeed_issues


def calculate_audit_score(high_issues: int, medium_issues: int, low_issues: int, total_pages: int) -> int:
    """
    Calculate an overall SEO score based on issues found, weighted by severity.

    Score calculation uses weighted penalties:
    - HIGH severity issues: 10 points penalty per issue per page
    - MEDIUM severity issues: 4 points penalty per issue per page  
    - LOW severity issues: 1 point penalty per issue per page

    Score calibration (moderate difficulty):
    - 0 issues/page = 100
    - Mix of 1 HIGH + 2 MEDIUM + 3 LOW per page = 71 points (good target)
    - 2 HIGH + 3 MEDIUM + 5 LOW per page = 53 points (needs work)
    - 5+ HIGH per page = <50 points (critical issues)

    Args:
        high_issues: Number of HIGH severity issues found
        medium_issues: Number of MEDIUM severity issues found
        low_issues: Number of LOW severity issues found
        total_pages: Total number of pages audited

    Returns:
        Score from 0-100
    """
    if total_pages == 0:
        return 100

    # Calculate weighted penalty per page
    avg_high_penalty = (high_issues / total_pages) * SCORE_PENALTY_HIGH
    avg_medium_penalty = (medium_issues / total_pages) * SCORE_PENALTY_MEDIUM
    avg_low_penalty = (low_issues / total_pages) * SCORE_PENALTY_LOW
    
    total_penalty = avg_high_penalty + avg_medium_penalty + avg_low_penalty
    score = max(0, 100 - total_penalty)

    return int(score)


def execute_audit_run(
    audit_run, pages=None, show_progress=True, debug=False, skip_pagespeed=False
):
    """
    Execute an audit run on the provided pages.

    This is the core audit execution function that can be called by both
    the CLI command and the scheduled audit command.

    Args:
        audit_run: The SEOAuditRun instance to execute
        pages: List of pages to audit (if None, will audit all live pages)
        show_progress: Whether to show progress bar (default: True)
        debug: Enable debug output (default: False)
        skip_pagespeed: Skip PageSpeed checks (default: False)

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
        results = run_audit_on_pages(
            pages,
            audit_run,
            show_progress=show_progress,
            debug=debug,
            skip_pagespeed=skip_pagespeed,
        )
        return results

    except Exception as e:
        # Mark audit as failed
        audit_run.status = "failed"
        audit_run.save()
        raise e
