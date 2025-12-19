# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Redirect auditing utilities for detecting chains, loops, and 404 targets.
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


def audit_redirects(
    site=None,
    check_external: bool = True,
) -> Dict[str, Any]:
    """
    Run a comprehensive audit of all redirects.

    Args:
        site: Optional Site instance. If None, audits all sites.
        check_external: Whether to check external URLs (may be slow).

    Returns:
        Dictionary with audit results including:
        - total_redirects: Total count of redirects
        - chains: List of redirect chains (longer than 1 hop)
        - loops: List of circular redirect loops
        - redirects_to_404: List of redirects pointing to 404 pages
        - redirects_to_unpublished: List of redirects to unpublished pages
        - external_redirects: Count of external redirects
        - statistics: Additional statistics (age distribution, etc.)
    """
    from wagtail.contrib.redirects.models import Redirect
    from wagtail.models import Site

    if site:
        sites = [site]
    else:
        sites = Site.objects.all()

    results = {
        "total_redirects": 0,
        "chains": [],
        "loops": [],
        "redirects_to_404": [],
        "redirects_to_unpublished": [],
        "external_redirects": 0,
        "statistics": {
            "by_age": {
                "less_than_30_days": 0,
                "30_to_90_days": 0,
                "90_to_365_days": 0,
                "over_365_days": 0,
            },
            "permanent_vs_temporary": {
                "permanent": 0,
                "temporary": 0,
            },
        },
    }

    for current_site in sites:
        site_redirects = Redirect.objects.filter(site=current_site)
        results["total_redirects"] += site_redirects.count()

        logger.info(f"Auditing site: {current_site}")

        # Detect chains
        chains = detect_redirect_chains(current_site)
        results["chains"].extend(chains)
        logger.info(f"Chains detected: {len(chains)}")

        # Detect loops
        loops = detect_circular_loops(current_site)
        results["loops"].extend(loops)
        logger.info(f"Loops detected: {len(loops)}")

        # Detect 404 targets
        redirects_404, redirects_unpublished = detect_404_redirects(
            current_site,
            check_external=check_external,
        )
        results["redirects_to_404"].extend(redirects_404)
        results["redirects_to_unpublished"].extend(redirects_unpublished)

        # Count external redirects
        external_count = (
            site_redirects.filter(
                redirect_page__isnull=True,
                redirect_link__isnull=False,
            )
            .exclude(redirect_link="")
            .count()
        )
        results["external_redirects"] += external_count

        # Calculate statistics
        _calculate_redirect_statistics(site_redirects, results["statistics"])

    # Also check global redirects (site_id=None) - these apply to all sites
    global_redirects = Redirect.objects.filter(site__isnull=True)
    global_count = global_redirects.count()

    if global_count > 0:
        logger.info(f"Auditing global redirects (no site assigned): {global_count}")
        results["total_redirects"] += global_count

        # Detect chains for global redirects
        chains = detect_redirect_chains(site=None)
        results["chains"].extend(chains)
        logger.info(f"Global chains detected: {len(chains)}")

        # Detect loops for global redirects
        loops = detect_circular_loops(site=None)
        results["loops"].extend(loops)
        logger.info(f"Global loops detected: {len(loops)}")

        # Detect 404 targets for global redirects
        redirects_404, redirects_unpublished = detect_404_redirects(
            site=None,
            check_external=check_external,
        )
        results["redirects_to_404"].extend(redirects_404)
        results["redirects_to_unpublished"].extend(redirects_unpublished)

        # Count external redirects in global
        external_count = (
            global_redirects.filter(
                redirect_page__isnull=True,
                redirect_link__isnull=False,
            )
            .exclude(redirect_link="")
            .count()
        )
        results["external_redirects"] += external_count

        # Calculate statistics for global redirects
        _calculate_redirect_statistics(global_redirects, results["statistics"])

    return results


def detect_redirect_chains(site) -> List[Dict[str, Any]]:
    """
    Detect redirect chains longer than 1 hop.

    A chain exists when redirect A -> B and there's another redirect B -> C.

    Args:
        site: The Wagtail Site instance, or None for global redirects

    Returns:
        List of chain dictionaries with:
        - chain_path: List of paths in the chain (e.g., ['/old', '/middle', '/new'])
        - hops: Number of hops in the chain
        - start_redirect_id: ID of the first redirect in the chain
        - site_name: Name of the site
    """
    from wagtail.contrib.redirects.models import Redirect

    chains = []
    visited = set()

    # Handle both site-specific and global (site=None) redirects
    if site is None:
        redirects = Redirect.objects.filter(site__isnull=True).select_related(
            "redirect_page"
        )
        site_name = "Global (no site)"
    else:
        redirects = Redirect.objects.filter(site=site).select_related("redirect_page")
        site_name = site.site_name if site.site_name else str(site)

    # Build a mapping of old_path -> redirect for quick lookup
    path_to_redirect = {}
    for redirect in redirects:
        normalized_path = redirect.old_path.rstrip("/") or "/"
        path_to_redirect[normalized_path] = redirect

    for redirect in redirects:
        if redirect.id in visited:
            continue

        chain_path = [redirect.old_path]
        current_redirect = redirect
        chain_redirects = [redirect.id]

        # Follow the chain
        while True:
            target_path = _get_redirect_target_path(current_redirect)
            if not target_path:
                break

            normalized_target = target_path.rstrip("/") or "/"
            chain_path.append(target_path)

            # Check if target has another redirect
            next_redirect = path_to_redirect.get(normalized_target)
            if not next_redirect or next_redirect.id in chain_redirects:
                break

            chain_redirects.append(next_redirect.id)
            current_redirect = next_redirect

        # If chain has more than 2 paths (more than 1 hop), record it
        if len(chain_path) > 2:
            chains.append(
                {
                    "chain_path": chain_path,
                    "hops": len(chain_path) - 1,
                    "start_redirect_id": redirect.id,
                    "site_name": site_name,
                }
            )
            visited.update(chain_redirects)

    return chains


def detect_circular_loops(site) -> List[Dict[str, Any]]:
    """
    Detect circular redirect loops.

    A loop exists when following redirects eventually leads back to the start.
    Example: A -> B -> C -> A

    Args:
        site: The Wagtail Site instance, or None for global redirects

    Returns:
        List of loop dictionaries with:
        - loop_path: List of paths in the loop
        - redirect_ids: List of redirect IDs involved
        - site_name: Name of the site
    """
    from wagtail.contrib.redirects.models import Redirect

    loops = []
    found_loop_sets = set()

    # Handle both site-specific and global (site=None) redirects
    if site is None:
        redirects = Redirect.objects.filter(site__isnull=True).select_related(
            "redirect_page"
        )
        site_name = "Global (no site)"
    else:
        redirects = Redirect.objects.filter(site=site).select_related("redirect_page")
        site_name = site.site_name if site.site_name else str(site)

    # Build a mapping of old_path -> redirect for quick lookup
    path_to_redirect = {}
    for redirect in redirects:
        normalized_path = redirect.old_path.rstrip("/") or "/"
        path_to_redirect[normalized_path] = redirect

    for redirect in redirects:
        visited_paths = set()
        path_list = []
        redirect_ids = []
        current_redirect = redirect
        start_path = redirect.old_path.rstrip("/") or "/"

        while current_redirect:
            current_path = current_redirect.old_path.rstrip("/") or "/"

            # Check if we've seen this path before (loop detected)
            if current_path in visited_paths:
                # Found a loop - extract just the loop portion
                loop_start_idx = path_list.index(current_path)
                loop_path = path_list[loop_start_idx:]
                loop_redirect_ids = redirect_ids[loop_start_idx:]

                # Create a hashable key to avoid duplicate loops
                loop_key = frozenset(loop_redirect_ids)
                if loop_key not in found_loop_sets:
                    found_loop_sets.add(loop_key)
                    loops.append(
                        {
                            "loop_path": loop_path + [current_path],  # Close the loop
                            "redirect_ids": loop_redirect_ids,
                            "site_name": site_name,
                        }
                    )
                break

            visited_paths.add(current_path)
            path_list.append(current_path)
            redirect_ids.append(current_redirect.id)

            # Get target and find next redirect
            target_path = _get_redirect_target_path(current_redirect)
            if not target_path:
                break

            normalized_target = target_path.rstrip("/") or "/"
            current_redirect = path_to_redirect.get(normalized_target)

    return loops


def detect_404_redirects(
    site, check_external: bool = True
) -> Tuple[List[Dict], List[Dict]]:
    """
    Detect redirects pointing to 404/deleted pages or unpublished pages.

    Args:
        site: The Wagtail Site instance, or None for global redirects
        check_external: Whether to check external URLs (may be slow)

    Returns:
        Tuple of (redirects_to_404, redirects_to_unpublished) lists
    """
    from wagtail.contrib.redirects.models import Redirect
    from wagtail.models import Page

    redirects_to_404 = []
    redirects_to_unpublished = []

    # Handle both site-specific and global (site=None) redirects
    if site is None:
        redirects = Redirect.objects.filter(site__isnull=True).select_related(
            "redirect_page"
        )
        site_name = "Global (no site)"
    else:
        redirects = Redirect.objects.filter(site=site).select_related("redirect_page")
        site_name = site.site_name if site.site_name else str(site)

    total_redirects = redirects.count()

    logger.info(
        f"Checking {total_redirects} redirects for 404 targets on '{site_name}'"
    )

    page_redirects_count = 0
    link_redirects_count = 0
    external_checked_count = 0

    for redirect in redirects:
        # Check page-based redirects
        if redirect.redirect_page_id:
            page_redirects_count += 1
            logger.debug(
                f"Checking page redirect: {redirect.old_path} -> page_id={redirect.redirect_page_id}"
            )
            try:
                page = Page.objects.get(id=redirect.redirect_page_id)
                if not page.live:
                    logger.info(
                        f"Found redirect to unpublished page: {redirect.old_path} -> '{page.title}' (page_id={page.id})"
                    )
                    redirects_to_unpublished.append(
                        {
                            "redirect_id": redirect.id,
                            "old_path": redirect.old_path,
                            "target_page_id": page.id,
                            "target_page_title": page.title,
                            "site_name": site_name,
                            "reason": "Page is unpublished",
                        }
                    )
                else:
                    logger.debug(
                        f"Page redirect OK: {redirect.old_path} -> '{page.title}'"
                    )
            except Page.DoesNotExist:
                # Page was deleted
                logger.warning(
                    f"Found redirect to deleted page: {redirect.old_path} -> page_id={redirect.redirect_page_id}"
                )
                redirects_to_404.append(
                    {
                        "redirect_id": redirect.id,
                        "old_path": redirect.old_path,
                        "target": f"Page ID {redirect.redirect_page_id} (deleted)",
                        "site_name": site_name,
                        "reason": "Target page has been deleted",
                    }
                )

        # Check link-based redirects (internal paths)
        elif redirect.redirect_link:
            link_redirects_count += 1
            link = redirect.redirect_link
            parsed = urlparse(link)

            # Check if it's an internal path (no scheme/netloc or same domain)
            is_internal = not parsed.scheme or not parsed.netloc

            if is_internal:
                # Check if internal path exists as a page
                # Skip for global redirects (site=None) since we can't know which site to check
                if site is None:
                    logger.debug(
                        f"Skipping internal path check for global redirect: {redirect.old_path} -> {link}"
                    )
                else:
                    path = parsed.path.rstrip("/") or "/"
                    logger.debug(
                        f"Checking internal link redirect: {redirect.old_path} -> {link}"
                    )
                    page_exists = _check_internal_path_exists(site, path)
                    if not page_exists:
                        logger.info(
                            f"Found redirect to non-existent internal path: {redirect.old_path} -> {link}"
                        )
                        redirects_to_404.append(
                            {
                                "redirect_id": redirect.id,
                                "old_path": redirect.old_path,
                                "target": link,
                                "site_name": site_name,
                                "reason": "Internal path does not match any page",
                            }
                        )
                    else:
                        logger.debug(
                            f"Internal link redirect OK: {redirect.old_path} -> {link}"
                        )
            elif check_external:
                # Check external URL (with rate limiting consideration)
                external_checked_count += 1
                logger.debug(
                    f"Checking external URL redirect: {redirect.old_path} -> {link}"
                )
                is_valid = _check_external_url(link)
                if not is_valid:
                    logger.warning(
                        f"Found redirect to unreachable external URL: {redirect.old_path} -> {link}"
                    )
                    redirects_to_404.append(
                        {
                            "redirect_id": redirect.id,
                            "old_path": redirect.old_path,
                            "target": link,
                            "site_name": site_name,
                            "reason": "External URL returns 404 or is unreachable",
                        }
                    )
                else:
                    logger.debug(
                        f"External URL redirect OK: {redirect.old_path} -> {link}"
                    )
            else:
                logger.debug(
                    f"Skipping external URL check (disabled): {redirect.old_path} -> {link}"
                )

    logger.info(
        f"404 check complete for '{site_name}': "
        f"checked {page_redirects_count} page redirects, "
        f"{link_redirects_count} link redirects "
        f"({external_checked_count} external URLs checked). "
        f"Found {len(redirects_to_404)} 404s, {len(redirects_to_unpublished)} unpublished."
    )

    return redirects_to_404, redirects_to_unpublished


def get_redirect_statistics(site=None) -> Dict[str, Any]:
    """
    Get detailed statistics about redirects.

    Args:
        site: Optional Site instance. If None, gets stats for all sites.

    Returns:
        Dictionary with various statistics
    """
    from django.db.models import Count
    from wagtail.contrib.redirects.models import Redirect
    from wagtail.models import Site

    if site:
        redirects = Redirect.objects.filter(site=site)
    else:
        redirects = Redirect.objects.all()

    now = timezone.now()
    stats = {
        "total": redirects.count(),
        "by_site": {},
        "by_age": {
            "less_than_30_days": 0,
            "30_to_90_days": 0,
            "90_to_365_days": 0,
            "over_365_days": 0,
        },
        "by_type": {
            "to_page": redirects.filter(redirect_page__isnull=False).count(),
            "to_link": redirects.filter(
                redirect_page__isnull=True, redirect_link__isnull=False
            )
            .exclude(redirect_link="")
            .count(),
        },
        "permanent_count": redirects.filter(is_permanent=True).count(),
        "temporary_count": redirects.filter(is_permanent=False).count(),
    }

    # Count by site
    sites = Site.objects.all()
    for s in sites:
        site_count = redirects.filter(site=s).count()
        if site_count > 0:
            stats["by_site"][s.site_name or str(s)] = site_count

    # Age distribution (if redirects have created timestamp via auto_now_add)
    # Note: Wagtail's Redirect model doesn't have created_at by default,
    # so we'll skip this if the field doesn't exist
    if hasattr(Redirect, "created_at"):
        for redirect in redirects:
            if redirect.created_at:
                age = now - redirect.created_at
                if age < timedelta(days=30):
                    stats["by_age"]["less_than_30_days"] += 1
                elif age < timedelta(days=90):
                    stats["by_age"]["30_to_90_days"] += 1
                elif age < timedelta(days=365):
                    stats["by_age"]["90_to_365_days"] += 1
                else:
                    stats["by_age"]["over_365_days"] += 1

    return stats


def run_redirect_audit_and_flatten(site=None) -> Dict[str, Any]:
    """
    Run a complete redirect audit and flatten chains.

    This is the main entry point for the seoaudit command.

    Args:
        site: Optional Site instance. If None, processes all sites.

    Returns:
        Dictionary with:
        - audit_results: Results from audit_redirects()
        - chains_flattened: Number of chains flattened
    """
    from wagtail_seotoolkit.pro.utils.redirect_utils import flatten_all_redirect_chains

    # First, run the audit to get current state
    audit_results = audit_redirects(site)

    # Then flatten chains
    chains_flattened = flatten_all_redirect_chains(site)

    return {
        "audit_results": audit_results,
        "chains_flattened": chains_flattened,
    }


def _get_redirect_target_path(redirect) -> Optional[str]:
    """
    Get the target path of a redirect (either from page or link).

    Args:
        redirect: The Redirect instance

    Returns:
        The target path string, or None if not available
    """
    if redirect.redirect_page:
        try:
            url = redirect.redirect_page.url
            if url:
                return url.rstrip("/") or "/"
        except Exception:
            pass
    elif redirect.redirect_link:
        parsed = urlparse(redirect.redirect_link)
        # Return just the path for internal links
        if not parsed.scheme or not parsed.netloc:
            return redirect.redirect_link.rstrip("/") or "/"
        # For external links, return the full URL
        return redirect.redirect_link

    return None


def _check_internal_path_exists(site, path: str) -> bool:
    """
    Check if an internal path exists as a live page.

    Args:
        site: The Wagtail Site instance
        path: The path to check

    Returns:
        True if the path matches a live page
    """
    from wagtail.models import Page

    # Normalize path
    normalized_path = path.rstrip("/") or "/"

    # Try to find a page at this path
    try:
        root_page = site.root_page
        if normalized_path == "/":
            return root_page.live

        # Route through the page tree
        path_parts = [p for p in normalized_path.split("/") if p]
        current_page = root_page

        for part in path_parts:
            try:
                current_page = current_page.get_children().get(slug=part)
            except Page.DoesNotExist:
                return False

        return current_page.live
    except Exception:
        return False


def _check_external_url(url: str, timeout: int = 5) -> bool:
    """
    Check if an external URL is reachable and doesn't return 404.

    Args:
        url: The URL to check
        timeout: Request timeout in seconds

    Returns:
        True if URL is reachable and returns 2xx/3xx status
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False


def _calculate_redirect_statistics(redirects, stats: Dict[str, Any]) -> None:
    """
    Calculate redirect statistics and update the stats dictionary.

    Args:
        redirects: QuerySet of redirects
        stats: Statistics dictionary to update
    """
    for redirect in redirects:
        # Permanent vs temporary
        if redirect.is_permanent:
            stats["permanent_vs_temporary"]["permanent"] += 1
        else:
            stats["permanent_vs_temporary"]["temporary"] += 1
