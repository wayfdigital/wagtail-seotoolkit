"""
PageSpeed Insights API client for SEO audits.

This module provides functions to interact with Google's PageSpeed Insights API,
including rate limiting, mock data for testing, and response parsing.
"""

import re
import time
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings


def get_pagespeed_settings() -> Dict[str, Any]:
    """Get PageSpeed configuration from Django settings."""
    return {
        "api_key": getattr(settings, "WAGTAIL_SEOTOOLKIT_PAGESPEED_API_KEY", None),
        "enabled": getattr(settings, "WAGTAIL_SEOTOOLKIT_PAGESPEED_ENABLED", True),
        "dry_run": getattr(settings, "WAGTAIL_SEOTOOLKIT_PAGESPEED_DRY_RUN", False),
        "per_page_type": getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE", False
        ),
    }


def get_mock_pagespeed_data() -> Dict[str, Any]:
    """Return mock PageSpeed Insights data for dry-run testing."""
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {
                    "id": "performance",
                    "title": "Performance",
                    "score": 0.75,  # 75/100 - triggers medium severity
                },
                "accessibility": {
                    "id": "accessibility",
                    "title": "Accessibility",
                    "score": 0.85,  # 85/100 - triggers medium severity
                },
                "best-practices": {
                    "id": "best-practices",
                    "title": "Best Practices",
                    "score": 0.45,  # 45/100 - triggers high severity
                },
                "seo": {
                    "id": "seo",
                    "title": "SEO",
                    "score": 0.92,  # 92/100 - no issue
                },
            },
            "audits": {
                "unused-css-rules": {
                    "id": "unused-css-rules",
                    "title": "Remove unused CSS",
                    "description": "Remove dead rules from stylesheets and defer the loading of CSS not used for above-the-fold content.",
                    "score": 0.0,  # Failed audit
                    "scoreDisplayMode": "numeric",
                    "displayValue": "Potential savings of 2.1 KiB",
                },
                "uses-text-compression": {
                    "id": "uses-text-compression",
                    "title": "Enable text compression",
                    "description": "Text-based resources should be served with compression (gzip, deflate or brotli) to minimize total network bytes.",
                    "score": 0.0,  # Failed audit
                    "scoreDisplayMode": "binary",
                },
            },
        }
    }


def call_pagespeed_api(
    url: str,
    api_key: Optional[str] = None,
    strategy: str = "mobile",
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Make API call to Google PageSpeed Insights.

    Args:
        url: The URL to test
        api_key: Google API key (optional)
        strategy: 'mobile' or 'desktop'
        debug: Enable debug logging

    Returns:
        PageSpeed Insights API response

    Raises:
        requests.RequestException: If API call fails
    """
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }

    if api_key:
        params["key"] = api_key

    if debug:
        print(f"[DEBUG] PageSpeed API call: {api_url}")
        print(f"[DEBUG] Parameters: {params}")

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if debug:
            print(f"[DEBUG] API Response status: {response.status_code}")
            print(f"[DEBUG] API Response keys: {list(data.keys())}")
            if "lighthouseResult" in data:
                print(
                    f"[DEBUG] Lighthouse categories: {list(data['lighthouseResult'].get('categories', {}).keys())}"
                )

        return data

    except requests.RequestException as e:
        if debug:
            print(f"[DEBUG] PageSpeed API error: {e}")
        raise


def parse_lighthouse_result(lighthouse_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Lighthouse result to extract scores and metrics.

    Args:
        lighthouse_data: The lighthouseResult from PageSpeed API response

    Returns:
        Dictionary with parsed scores and metrics
    """
    result = {"scores": {}, "metrics": {}, "failed_audits": []}

    # Extract category scores
    categories = lighthouse_data.get("categories", {})
    for category_id, category_data in categories.items():
        score = category_data.get("score")
        if score is not None:
            result["scores"][category_id] = int(score * 100)  # Convert to 0-100 scale

    # Extract key metrics
    audits = lighthouse_data.get("audits", {})
    metric_keys = [
        "first-contentful-paint",
        "largest-contentful-paint",
        "speed-index",
        "total-blocking-time",
        "cumulative-layout-shift",
        "interactive",
    ]

    for metric_key in metric_keys:
        if metric_key in audits:
            audit = audits[metric_key]
            result["metrics"][metric_key] = {
                "score": audit.get("score"),
                "displayValue": audit.get("displayValue"),
                "numericValue": audit.get("numericValue"),
            }

    # Find failed audits
    for audit_id, audit_data in audits.items():
        score = audit_data.get("score")
        score_display_mode = audit_data.get("scoreDisplayMode", "numeric")

        # Consider audit failed if:
        # - score is 0 or null for binary audits
        # - score < 0.9 for numeric audits
        if score is not None:
            if score_display_mode == "binary" and score < 1.0:
                result["failed_audits"].append(
                    {
                        "id": audit_id,
                        "title": audit_data.get("title", ""),
                        "description": audit_data.get("description", ""),
                        "score": score,
                        "displayValue": audit_data.get("displayValue", ""),
                    }
                )
            elif score_display_mode == "numeric" and score < 0.9:
                result["failed_audits"].append(
                    {
                        "id": audit_id,
                        "title": audit_data.get("title", ""),
                        "description": audit_data.get("description", ""),
                        "score": score,
                        "displayValue": audit_data.get("displayValue", ""),
                    }
                )

    return result


def convert_markdown_links_to_html(text: str) -> str:
    """
    Convert markdown-style links to HTML links.

    Args:
        text: Text that may contain markdown links like [text](url)

    Returns:
        Text with HTML links
    """
    # Pattern to match markdown links: [text](url)
    markdown_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replace_link(match):
        link_text = match.group(1)
        link_url = match.group(2)
        return f'<a href="{link_url}" target="_blank" rel="noopener noreferrer">{link_text}</a>'

    return re.sub(markdown_link_pattern, replace_link, text)


def generate_issues_from_audits(
    audits: List[Dict[str, Any]], url: str
) -> List[Dict[str, Any]]:
    """
    Convert Lighthouse audit failures to SEO audit issues.

    Args:
        audits: List of failed audit data
        url: The URL being audited

    Returns:
        List of issue dictionaries
    """
    issues = []

    for audit in audits:
        # Convert markdown links in description to HTML
        description_html = convert_markdown_links_to_html(audit["description"])

        issues.append(
            {
                "issue_type": "pagespeed_lighthouse_audit_failed",
                "issue_severity": "medium",  # Will be overridden by model logic
                "description": f"Lighthouse audit failed: {audit['title']}. {description_html}",
                "page_url": url,
                "audit_title": audit["title"],
                "audit_description": audit["description"],
            }
        )

    return issues


def generate_issues_from_scores(
    scores: Dict[str, int], url: str
) -> List[Dict[str, Any]]:
    """
    Generate issues based on category scores.

    Args:
        scores: Dictionary of category scores (0-100)
        url: The URL being audited

    Returns:
        List of issue dictionaries
    """
    issues = []

    # Score thresholds
    LOW_THRESHOLD = 90
    CRITICAL_THRESHOLD = 50

    category_mapping = {
        "performance": (
            "pagespeed_performance_score_low",
            "pagespeed_performance_score_critical",
        ),
        "accessibility": (
            "pagespeed_accessibility_score_low",
            "pagespeed_accessibility_score_critical",
        ),
        "best-practices": (
            "pagespeed_best_practices_score_low",
            "pagespeed_best_practices_score_critical",
        ),
        "seo": ("pagespeed_seo_score_low", "pagespeed_seo_score_critical"),
    }

    for category, score in scores.items():
        if category not in category_mapping:
            continue

        low_issue, critical_issue = category_mapping[category]

        if score < CRITICAL_THRESHOLD:
            issues.append(
                {
                    "issue_type": critical_issue,
                    "issue_severity": "high",
                    "description": f"{category.title()} score is critically low ({score}/100). This significantly impacts user experience and SEO rankings.",
                    "page_url": url,
                    "score": score,
                }
            )
        elif score < LOW_THRESHOLD:
            issues.append(
                {
                    "issue_type": low_issue,
                    "issue_severity": "medium",
                    "description": f"{category.title()} score is {score}/100. Consider optimizing images, reducing JavaScript, and improving server response times.",
                    "page_url": url,
                    "score": score,
                }
            )

    return issues


def rate_limit_sleep():
    """Sleep for 1 second to respect API rate limits."""
    time.sleep(1)
