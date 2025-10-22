"""
PageSpeed Insights checker for SEO audits.

This checker integrates Google PageSpeed Insights API to analyze page performance,
accessibility, best practices, and SEO scores.
"""
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from wagtail_seotoolkit.utils.checkers.base import BaseChecker
from wagtail_seotoolkit.utils.pagespeed_api import (
    call_pagespeed_api,
    generate_issues_from_audits,
    generate_issues_from_scores,
    get_mock_pagespeed_data,
    get_pagespeed_settings,
    parse_lighthouse_result,
    rate_limit_sleep,
)


class PageSpeedChecker(BaseChecker):
    """Checker for PageSpeed Insights metrics."""

    def __init__(self, soup: BeautifulSoup, url: str = "", base_domain: str = "", debug: bool = False):
        """
        Initialize the PageSpeed checker.

        Args:
            soup: BeautifulSoup instance of the HTML
            url: The URL of the page being audited
            base_domain: The base domain to identify internal links
            debug: Enable debug output
        """
        super().__init__(soup, url, base_domain)
        self.debug = debug
        self.settings = get_pagespeed_settings()

    def check(self) -> List[Dict[str, Any]]:
        """
        Run PageSpeed Insights checks.

        Returns:
            List of issues found
        """
        self.issues = []

        # Skip if PageSpeed checks are disabled
        if not self.settings['enabled']:
            if self.debug:
                print("[DEBUG] PageSpeed checks disabled in settings")
            return self.issues

        # Skip if no API key and not in dry-run mode
        if not self.settings['api_key'] and not self.settings['dry_run']:
            if self.debug:
                print("[DEBUG] No PageSpeed API key configured, skipping checks")
            return self.issues

        # Skip if no URL provided
        if not self.url:
            if self.debug:
                print("[DEBUG] No URL provided for PageSpeed check")
            return self.issues

        try:
            # Get PageSpeed data
            if self.settings['dry_run']:
                if self.debug:
                    print(f"[DEBUG] Using mock PageSpeed data for {self.url}")
                pagespeed_data = get_mock_pagespeed_data()
            else:
                if self.debug:
                    print(f"[DEBUG] Making PageSpeed API call for {self.url}")
                pagespeed_data = call_pagespeed_api(
                    self.url, 
                    self.settings['api_key'], 
                    strategy='mobile',  # Use mobile as specified
                    debug=self.debug
                )
                # Rate limit after API call
                rate_limit_sleep()

            # Parse the results
            lighthouse_result = pagespeed_data.get('lighthouseResult', {})
            parsed_data = parse_lighthouse_result(lighthouse_result)

            # Generate issues from scores
            score_issues = generate_issues_from_scores(parsed_data['scores'], self.url)
            self.issues.extend(score_issues)

            # Generate issues from failed audits
            audit_issues = generate_issues_from_audits(parsed_data['failed_audits'], self.url)
            self.issues.extend(audit_issues)

            if self.debug:
                print(f"[DEBUG] PageSpeed check completed for {self.url}")
                print(f"[DEBUG] Found {len(self.issues)} issues")

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] PageSpeed check failed for {self.url}: {e}")
            # Don't raise exception, just log and continue
            # This prevents PageSpeed API issues from breaking the entire audit

        return self.issues
