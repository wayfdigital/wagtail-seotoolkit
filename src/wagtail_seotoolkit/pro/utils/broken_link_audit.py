# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Broken link detection utilities for scanning pages for non-working links.

Uses Wagtail's ReferenceIndex to find internal page links and checks their status.
Also scans RichText content for external links.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.urls import reverse

logger = logging.getLogger(__name__)


def audit_broken_links(
    site=None,
    check_external: bool = False,
    limit_pages: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Scan all pages for broken internal and external links.

    Args:
        site: Optional Site instance. If None, scans all sites.
        check_external: Whether to check external URLs (slow, makes HTTP requests).
        limit_pages: Optional limit on number of pages to scan.

    Returns:
        Dictionary with:
        - total_pages_scanned: Number of pages checked
        - total_links_checked: Number of links checked
        - broken_internal_links: List of broken internal link details
        - links_to_unpublished: List of links to unpublished pages
        - broken_external_links: List of broken external link details (if check_external=True)
    """
    from wagtail.models import Page, Site

    results = {
        "total_pages_scanned": 0,
        "total_links_checked": 0,
        "broken_internal_links": [],
        "links_to_unpublished": [],
        "broken_external_links": [],
    }

    # Get pages to scan
    if site:
        pages = Page.objects.live().descendant_of(site.root_page, inclusive=True)
    else:
        pages = Page.objects.live()

    # Exclude root pages
    pages = pages.exclude(depth__lte=1)

    if limit_pages:
        pages = pages[:limit_pages]

    pages = pages.specific()
    total_pages = pages.count()

    logger.info(f"Scanning {total_pages} pages for broken links")

    for page in pages:
        results["total_pages_scanned"] += 1

        # Check internal links using ReferenceIndex
        internal_broken, internal_unpublished, links_count = _check_page_internal_links(
            page
        )
        results["broken_internal_links"].extend(internal_broken)
        results["links_to_unpublished"].extend(internal_unpublished)
        results["total_links_checked"] += links_count

        # Check external links in RichText content
        if check_external:
            external_broken, ext_links_count = _check_page_external_links(page)
            results["broken_external_links"].extend(external_broken)
            results["total_links_checked"] += ext_links_count

    logger.info(
        f"Broken link scan complete: {results['total_pages_scanned']} pages, "
        f"{results['total_links_checked']} links checked. "
        f"Found {len(results['broken_internal_links'])} broken internal, "
        f"{len(results['links_to_unpublished'])} to unpublished, "
        f"{len(results['broken_external_links'])} broken external."
    )

    return results


def _check_page_internal_links(page) -> Tuple[List[Dict], List[Dict], int]:
    """
    Check all internal page links from a page by scanning content fields.

    Scans RichText and StreamField content for page links (linktype="page")
    and checks if target pages exist and are published.

    Args:
        page: The Page instance to check outgoing links from.

    Returns:
        Tuple of (broken_links, links_to_unpublished, total_links_count)
    """
    from wagtail.fields import RichTextField, StreamField
    from wagtail.models import Page

    broken_links = []
    links_to_unpublished = []
    links_count = 0
    checked_page_ids = set()  # Avoid duplicate checks for same target

    try:
        specific_page = page.specific if hasattr(page, "specific") else page

        for field in specific_page._meta.get_fields():
            field_name = field.name

            # Skip relation fields
            if field.is_relation and not field.concrete:
                continue

            try:
                field_value = getattr(specific_page, field_name, None)
                if not field_value:
                    continue

                # Check RichTextField content for page links
                if isinstance(field, RichTextField):
                    page_ids = _extract_page_ids_from_richtext(str(field_value))
                    for target_id in page_ids:
                        if target_id in checked_page_ids:
                            continue
                        checked_page_ids.add(target_id)
                        links_count += 1

                        broken, unpublished = _check_page_link(
                            page, target_id, field_name
                        )
                        if broken:
                            broken_links.append(broken)
                        if unpublished:
                            links_to_unpublished.append(unpublished)

                # Check StreamField content for page links
                elif isinstance(field, StreamField) and field_value:
                    page_ids = _extract_page_ids_from_streamfield(field_value)
                    for target_id in page_ids:
                        if target_id in checked_page_ids:
                            continue
                        checked_page_ids.add(target_id)
                        links_count += 1

                        broken, unpublished = _check_page_link(
                            page, target_id, field_name
                        )
                        if broken:
                            broken_links.append(broken)
                        if unpublished:
                            links_to_unpublished.append(unpublished)

            except Exception as e:
                logger.debug(f"Error checking field {field_name}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Error checking internal links for page {page.pk}: {e}")

    return broken_links, links_to_unpublished, links_count


def _check_page_link(
    source_page, target_page_id: int, field_name: str
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Check if a page link target exists and is published.

    Returns:
        Tuple of (broken_link_record or None, unpublished_link_record or None)
    """
    from wagtail.models import Page

    try:
        target_page = Page.objects.get(id=target_page_id)

        if not target_page.live:
            logger.debug(
                f"Found link to unpublished page: {source_page.title} -> {target_page.title}"
            )
            return None, _create_broken_link_record(
                source_page=source_page,
                target_id=target_page_id,
                target_title=target_page.title,
                target_url=target_page.url,
                field_path=field_name,
                reason="Target page is unpublished",
                link_type="internal",
            )
        return None, None

    except Page.DoesNotExist:
        logger.debug(
            f"Found broken internal link: {source_page.title} -> Page ID {target_page_id} (deleted)"
        )
        return _create_broken_link_record(
            source_page=source_page,
            target_id=target_page_id,
            target_title=f"Page ID {target_page_id}",
            target_url=None,
            field_path=field_name,
            reason="Target page has been deleted",
            link_type="internal",
        ), None


def _extract_page_ids_from_richtext(html_content: str) -> List[int]:
    """
    Extract page IDs from RichText HTML content (linktype="page" links).

    Args:
        html_content: The HTML content to scan.

    Returns:
        List of page IDs found.
    """
    page_ids = []

    if not html_content:
        return page_ids

    # Pattern to match Wagtail page links: <a linktype="page" id="123">
    # Also handles variations like <a id="123" linktype="page">
    patterns = [
        r'linktype=["\']page["\'][^>]*id=["\'](\d+)["\']',
        r'id=["\'](\d+)["\'][^>]*linktype=["\']page["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html_content):
            try:
                page_id = int(match.group(1))
                if page_id not in page_ids:
                    page_ids.append(page_id)
            except ValueError:
                continue

    return page_ids


def _extract_page_ids_from_streamfield(stream_value) -> List[int]:
    """
    Extract page IDs from StreamField content.

    Args:
        stream_value: The StreamField value to scan.

    Returns:
        List of page IDs found.
    """
    page_ids = []

    try:
        # Method 1: Iterate over blocks directly to get RichText values
        for block in stream_value:
            block_value = block.value

            # Check if this is a RichText value (has 'source' attribute)
            if hasattr(block_value, "source"):
                html_content = block_value.source
                if html_content and (
                    'linktype="page"' in html_content
                    or "linktype='page'" in html_content
                ):
                    page_ids.extend(_extract_page_ids_from_richtext(html_content))
            # Check if it's a string (plain RichText HTML)
            elif isinstance(block_value, str):
                if 'linktype="page"' in block_value or "linktype='page'" in block_value:
                    page_ids.extend(_extract_page_ids_from_richtext(block_value))
            # Check if it's a StructBlock or similar (dict-like)
            elif hasattr(block_value, "items") or isinstance(block_value, dict):
                page_ids.extend(
                    _find_page_ids_in_data(
                        dict(block_value)
                        if hasattr(block_value, "items")
                        else block_value
                    )
                )
            # Check if it's a ListBlock (iterable)
            elif hasattr(block_value, "__iter__") and not isinstance(block_value, str):
                try:
                    for item in block_value:
                        if hasattr(item, "source"):
                            if item.source and (
                                'linktype="page"' in item.source
                                or "linktype='page'" in item.source
                            ):
                                page_ids.extend(
                                    _extract_page_ids_from_richtext(item.source)
                                )
                        elif isinstance(item, str):
                            if 'linktype="page"' in item or "linktype='page'" in item:
                                page_ids.extend(_extract_page_ids_from_richtext(item))
                except (TypeError, AttributeError):
                    pass

        # Method 2: Also check raw_data as fallback
        if hasattr(stream_value, "raw_data"):
            stream_data = list(stream_value.raw_data)
            page_ids.extend(_find_page_ids_in_data(stream_data))

    except Exception as e:
        logger.debug(f"Error extracting page IDs from StreamField: {e}")

    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for pid in page_ids:
        if pid not in seen:
            seen.add(pid)
            unique_ids.append(pid)

    return unique_ids


def _find_page_ids_in_data(data) -> List[int]:
    """
    Recursively find page IDs in nested data structure.
    """
    page_ids = []

    if isinstance(data, dict):
        for key, value in data.items():
            # Check for page chooser fields (page, related_page, etc.)
            if key in ("page", "related_page", "link_page", "internal_page"):
                if isinstance(value, int):
                    page_ids.append(value)
                elif isinstance(value, dict) and "id" in value:
                    page_ids.append(value["id"])
            # Check for RichText content in value or source fields
            elif key in ("value", "source") and isinstance(value, str):
                if 'linktype="page"' in value or "linktype='page'" in value:
                    page_ids.extend(_extract_page_ids_from_richtext(value))
            else:
                page_ids.extend(_find_page_ids_in_data(value))
    elif isinstance(data, list):
        for item in data:
            page_ids.extend(_find_page_ids_in_data(item))
    elif isinstance(data, str):
        # Check if string contains page links
        if 'linktype="page"' in data or "linktype='page'" in data:
            page_ids.extend(_extract_page_ids_from_richtext(data))

    return page_ids


def _check_page_external_links(page) -> Tuple[List[Dict], int]:
    """
    Check external links in RichText fields of a page.

    Args:
        page: The Page instance to check.

    Returns:
        Tuple of (broken_links, total_links_count)
    """
    from wagtail.fields import RichTextField, StreamField

    broken_links = []
    links_count = 0

    # Get all fields from the specific page model
    try:
        specific_page = page.specific if hasattr(page, "specific") else page

        for field in specific_page._meta.get_fields():
            field_name = field.name

            # Skip relation fields
            if field.is_relation and not field.concrete:
                continue

            try:
                field_value = getattr(specific_page, field_name, None)
                if not field_value:
                    continue

                # Check RichTextField content
                if isinstance(field, RichTextField):
                    urls = _extract_external_urls_from_richtext(str(field_value))
                    for url in urls:
                        links_count += 1
                        if not _check_external_url(url):
                            logger.debug(
                                f"Found broken external link: {page.title} -> {url}"
                            )
                            broken_links.append(
                                _create_broken_link_record(
                                    source_page=page,
                                    target_id=None,
                                    target_title=url,
                                    target_url=url,
                                    field_path=field_name,
                                    reason="External URL returns error or is unreachable",
                                    link_type="external",
                                )
                            )

                # Check StreamField content
                elif isinstance(field, StreamField) and field_value:
                    urls = _extract_external_urls_from_streamfield(field_value)
                    for url in urls:
                        links_count += 1
                        if not _check_external_url(url):
                            logger.debug(
                                f"Found broken external link in StreamField: {page.title} -> {url}"
                            )
                            broken_links.append(
                                _create_broken_link_record(
                                    source_page=page,
                                    target_id=None,
                                    target_title=url,
                                    target_url=url,
                                    field_path=field_name,
                                    reason="External URL returns error or is unreachable",
                                    link_type="external",
                                )
                            )

            except Exception as e:
                logger.debug(f"Error checking field {field_name}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Error checking external links for page {page.pk}: {e}")

    return broken_links, links_count


def _extract_external_urls_from_richtext(html_content: str) -> List[str]:
    """
    Extract external URLs from RichText HTML content.

    Args:
        html_content: The HTML content to scan.

    Returns:
        List of external URLs found.
    """
    urls = []

    if not html_content:
        return urls

    # Pattern to match href attributes with external URLs
    # Skip internal page links (linktype="page")
    href_pattern = r'href=["\']([^"\']+)["\']'

    for match in re.finditer(href_pattern, html_content):
        url = match.group(1)

        # Skip internal page links and anchors
        if url.startswith("#") or url.startswith("/"):
            continue

        # Skip Wagtail internal page links
        if "linktype=" in html_content[max(0, match.start() - 50) : match.end()]:
            continue

        # Check if it's an external URL
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            urls.append(url)

    return urls


def _extract_external_urls_from_streamfield(stream_value) -> List[str]:
    """
    Extract external URLs from StreamField content.

    Args:
        stream_value: The StreamField value to scan.

    Returns:
        List of external URLs found.
    """
    urls = []

    try:
        # Method 1: Iterate over blocks directly to get RichText values
        for block in stream_value:
            block_value = block.value

            # Check if this is a RichText value (has 'source' attribute)
            if hasattr(block_value, "source"):
                html_content = block_value.source
                if html_content and (
                    'href="http' in html_content or "href='http" in html_content
                ):
                    urls.extend(_extract_external_urls_from_richtext(html_content))
            # Check if it's a string (plain RichText HTML)
            elif isinstance(block_value, str):
                if 'href="http' in block_value or "href='http" in block_value:
                    urls.extend(_extract_external_urls_from_richtext(block_value))
            # Check if it's a StructBlock or similar (dict-like)
            elif hasattr(block_value, "items") or isinstance(block_value, dict):
                urls.extend(
                    _find_urls_in_data(
                        dict(block_value)
                        if hasattr(block_value, "items")
                        else block_value
                    )
                )
            # Check if it's a ListBlock (iterable)
            elif hasattr(block_value, "__iter__") and not isinstance(block_value, str):
                try:
                    for item in block_value:
                        if hasattr(item, "source"):
                            if item.source and (
                                'href="http' in item.source
                                or "href='http" in item.source
                            ):
                                urls.extend(
                                    _extract_external_urls_from_richtext(item.source)
                                )
                        elif isinstance(item, str):
                            if 'href="http' in item or "href='http" in item:
                                urls.extend(_extract_external_urls_from_richtext(item))
                except (TypeError, AttributeError):
                    pass

        # Method 2: Also check raw_data as fallback
        if hasattr(stream_value, "raw_data"):
            stream_data = list(stream_value.raw_data)
            urls.extend(_find_urls_in_data(stream_data))

    except Exception as e:
        logger.debug(f"Error extracting URLs from StreamField: {e}")

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def _find_urls_in_data(data) -> List[str]:
    """
    Recursively find external URLs in nested data structure.
    """
    urls = []

    if isinstance(data, dict):
        for key, value in data.items():
            # Check for URL fields
            if key in ("url", "link", "href", "external_link"):
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    urls.append(value)
            # Check for RichText content in value or source fields
            elif key in ("value", "source") and isinstance(value, str):
                if 'href="http' in value or "href='http" in value:
                    urls.extend(_extract_external_urls_from_richtext(value))
                # Also check for page links while we're here
            else:
                urls.extend(_find_urls_in_data(value))
    elif isinstance(data, list):
        for item in data:
            urls.extend(_find_urls_in_data(item))
    elif isinstance(data, str):
        # Check if string contains HTML with links
        if 'href="http' in data or "href='http" in data:
            urls.extend(_extract_external_urls_from_richtext(data))

    return urls


def _check_external_url(url: str, timeout: int = 10) -> bool:
    """
    Check if an external URL is reachable.

    Uses browser-like headers to avoid being blocked by bot protection.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.

    Returns:
        True if URL is reachable (2xx/3xx status).
    """
    # Browser-like headers to avoid bot detection
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        # Try HEAD request first (faster, less bandwidth)
        response = requests.head(
            url, timeout=timeout, allow_redirects=True, headers=headers
        )

        # Some servers return 405 Method Not Allowed for HEAD requests
        # In that case, try GET request
        if response.status_code == 405:
            response = requests.get(
                url, timeout=timeout, allow_redirects=True, headers=headers, stream=True
            )
            # Close the response immediately to not download content
            response.close()

        return response.status_code < 400

    except requests.RequestException:
        return False


def _create_broken_link_record(
    source_page,
    target_id: Optional[int],
    target_title: str,
    target_url: Optional[str],
    field_path: str,
    reason: str,
    link_type: str,
) -> Dict[str, Any]:
    """
    Create a broken link record dictionary.
    """
    try:
        edit_url = reverse("wagtailadmin_pages:edit", args=[source_page.pk])
    except Exception:
        edit_url = None

    return {
        "source_page_id": source_page.pk,
        "source_page_title": source_page.title,
        "source_page_url": source_page.url,
        "source_edit_url": edit_url,
        "target_id": target_id,
        "target_title": target_title,
        "target_url": target_url,
        "field_path": field_path,
        "reason": reason,
        "link_type": link_type,
    }


def get_broken_link_summary(audit_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of broken link audit results.

    Args:
        audit_results: Results from audit_broken_links()

    Returns:
        Summary dictionary with counts and health metrics.
    """
    total_broken = (
        len(audit_results["broken_internal_links"])
        + len(audit_results["links_to_unpublished"])
        + len(audit_results["broken_external_links"])
    )

    return {
        "total_pages_scanned": audit_results["total_pages_scanned"],
        "total_links_checked": audit_results["total_links_checked"],
        "broken_internal_count": len(audit_results["broken_internal_links"]),
        "links_to_unpublished_count": len(audit_results["links_to_unpublished"]),
        "broken_external_count": len(audit_results["broken_external_links"]),
        "total_broken": total_broken,
        "has_issues": total_broken > 0,
    }
