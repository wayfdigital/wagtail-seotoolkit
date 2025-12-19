"""
Signal handlers for automatic redirect creation on page URL changes.
"""

import logging

from .pro.utils.redirect_utils import create_redirect, is_auto_redirect_enabled

logger = logging.getLogger(__name__)


def create_redirect_on_slug_change(sender, instance, instance_before, **kwargs):
    """
    Signal handler for page_slug_changed.
    Creates a redirect when a page's slug is changed.
    """
    if not is_auto_redirect_enabled():
        return

    old_url = instance_before.url
    create_redirect(instance, old_url)


def create_redirect_on_page_move(
    sender, instance, url_path_before, url_path_after, **kwargs
):
    """
    Signal handler for post_page_move.
    Creates a redirect when a page is moved to a different section (URL changes).
    """
    if not is_auto_redirect_enabled():
        return

    # Only create redirect if URL actually changed (move, not reorder)
    if url_path_before == url_path_after:
        return

    # url_path is internal (e.g., /home/blog/post/), we need the public URL
    # The instance already has the new URL, so we construct the old one
    site = instance.get_site()
    if site:
        # Build old URL from url_path_before
        # url_path format: /home/parent/slug/ - we need to convert to public URL
        root_page = site.root_page
        root_url_path = root_page.url_path

        # Remove root page's url_path prefix to get relative path
        if url_path_before.startswith(root_url_path):
            old_relative_path = url_path_before[
                len(root_url_path) - 1 :
            ]  # Keep leading /
        else:
            old_relative_path = url_path_before

        create_redirect(instance, old_relative_path)


def delete_redirect_on_page_publish(sender, instance, **kwargs):
    """
    Signal handler for page_published.

    When a page is published, delete any redirect that has the same old_path
    as the page's URL. This handles the case where a page is created/published
    at a URL that was previously used as a redirect source.
    """
    from wagtail.contrib.redirects.models import Redirect

    page_url = instance.url
    if not page_url:
        return

    site = instance.get_site()
    if not site:
        return

    # Normalize the URL (remove trailing slash for comparison)
    page_path = page_url.rstrip("/") or "/"

    # Find and delete any redirects FROM this URL
    # Check both with and without trailing slash
    deleted_count, _ = Redirect.objects.filter(
        site=site,
        old_path__in=[page_path, page_path + "/"],
    ).delete()

    if deleted_count > 0:
        logger.info(
            f"Deleted {deleted_count} redirect(s) from '{page_path}' "
            f"because page '{instance.title}' was published at this URL"
        )


def register_signals():
    """
    Register all signal handlers for automatic redirect creation.
    """
    from wagtail.signals import page_published, page_slug_changed, post_page_move

    page_slug_changed.connect(create_redirect_on_slug_change)
    post_page_move.connect(create_redirect_on_page_move)
    page_published.connect(delete_redirect_on_page_publish)
