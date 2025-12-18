# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Utility functions for automatic redirect creation and chain flattening.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def is_auto_redirect_enabled():
    """Check if automatic redirect creation is enabled."""
    return getattr(settings, "WAGTAIL_SEOTOOLKIT_AUTO_REDIRECT_ON_SLUG_CHANGE", True)


def flatten_redirect_chains(site, new_redirect_old_path, target_page):
    """
    Detect and flatten redirect chains.

    When a new redirect A → B is created, this function:
    1. Finds all redirects pointing to A (e.g., X → A) and updates them to point to B (X → B)
    2. Checks if the target page B has any redirects pointing away from it,
       which would indicate a chain that needs flattening.

    This prevents redirect chains like A → B → C by flattening to A → C and B → C.

    Args:
        site: The Wagtail Site instance
        new_redirect_old_path: The old path that now redirects (normalized, no trailing slash)
        target_page: The page that the new redirect points to
    """
    from wagtail.contrib.redirects.models import Redirect

    flattened_count = 0

    # Step 1: Find redirects that point to the old_path (via redirect_link)
    # These are redirects like X → A where A is now redirecting to B
    # We need to update them to X → B
    #
    # redirect_link stores the URL path, check both with and without trailing slash
    old_path_variations = [new_redirect_old_path, new_redirect_old_path + "/"]

    redirects_to_old_path = Redirect.objects.filter(
        site=site,
        redirect_link__in=old_path_variations,
    )

    for redirect in redirects_to_old_path:
        old_target = redirect.redirect_link
        redirect.redirect_link = (
            ""  # Empty string, not None (Wagtail requires non-null)
        )
        redirect.redirect_page = target_page
        redirect.save()
        flattened_count += 1
        logger.info(
            f"Flattened redirect chain: {redirect.old_path} -> {old_target} -> {target_page.url} "
            f"(now: {redirect.old_path} -> {target_page.url})"
        )

    # Step 2: Find redirects where redirect_page points to pages that have
    # old_path as their URL. This handles the case where we have existing
    # redirects X → page_at_A, and page_at_A moved to B.
    # The page object is already updated, so we look for redirects pointing
    # to target_page that were created before this move.
    # (This is already handled by the page reference, but we log it)

    if flattened_count > 0:
        logger.info(f"Flattened {flattened_count} redirect chain(s) for site {site}")

    return flattened_count


def flatten_all_redirect_chains(site=None):
    """
    Audit and flatten all redirect chains for a site (or all sites).

    This function can be run as a nightly task to catch chains that emerge
    from multiple separate changes.

    Args:
        site: Optional Site instance. If None, processes all sites.

    Returns:
        Total number of redirects that were flattened.
    """
    from wagtail.contrib.redirects.models import Redirect
    from wagtail.models import Site

    total_flattened = 0

    if site:
        sites = [site]
    else:
        sites = Site.objects.all()

    for current_site in sites:
        # Get all redirects for this site that point to a page
        redirects = Redirect.objects.filter(
            site=current_site,
            redirect_page__isnull=False,
        ).select_related("redirect_page")

        for redirect in redirects:
            target_page = redirect.redirect_page
            if not target_page:
                continue

            # Get the target page's current URL path
            target_url = target_page.url
            if not target_url:
                continue

            # Normalize the target URL (remove trailing slash)
            target_path = target_url.rstrip("/") or "/"

            # Check if there's a redirect FROM the target path
            # This would indicate a chain: redirect.old_path → target_path → somewhere_else
            chain_redirect = Redirect.objects.filter(
                site=current_site,
                old_path=target_path,
            ).first()

            if chain_redirect:
                # We have a chain! Update the original redirect to point to the final destination
                if chain_redirect.redirect_page:
                    final_target = chain_redirect.redirect_page
                    old_target_path = target_path
                    redirect.redirect_page = final_target
                    redirect.redirect_link = (
                        ""  # Empty string, not None (Wagtail requires non-null)
                    )
                    redirect.save()
                    total_flattened += 1
                    logger.info(
                        f"Flattened chain: {redirect.old_path} -> {old_target_path} -> {final_target.url} "
                        f"(now: {redirect.old_path} -> {final_target.url})"
                    )
                elif chain_redirect.redirect_link:
                    final_link = chain_redirect.redirect_link
                    old_target_path = target_path
                    redirect.redirect_page = None
                    redirect.redirect_link = final_link
                    redirect.save()
                    total_flattened += 1
                    logger.info(
                        f"Flattened chain: {redirect.old_path} -> {old_target_path} -> {final_link} "
                        f"(now: {redirect.old_path} -> {final_link})"
                    )

    if total_flattened > 0:
        logger.info(f"Total redirects flattened in audit: {total_flattened}")

    return total_flattened


def create_redirect(page, old_path):
    """
    Create a redirect from old_path to the page and flatten any resulting chains.

    Args:
        page: The Wagtail Page instance to redirect to
        old_path: The old URL path to redirect from

    Returns:
        Tuple of (redirect, created) where redirect is the Redirect instance
        and created is a boolean indicating if it was newly created.
    """
    from wagtail.contrib.redirects.models import Redirect

    site = page.get_site()

    # Normalize old_path (remove trailing slash for consistency with Redirect model)
    old_path = old_path.rstrip("/") or "/"

    redirect, created = Redirect.objects.get_or_create(
        old_path=old_path,
        site=site,
        defaults={
            "redirect_page": page,
            "is_permanent": True,
        },
    )

    if created:
        logger.info(f"Created redirect: {old_path} -> {page.url}")
        # Flatten any redirect chains that may have been created
        flatten_redirect_chains(site, old_path, page)

    return redirect, created


def get_reference_count(page):
    """
    Get the number of references to a page using Wagtail's ReferenceIndex.

    Args:
        page: The Page instance to check references for.

    Returns:
        Integer count of references to the page.
    """
    from wagtail.models import ReferenceIndex

    return ReferenceIndex.get_references_to(page).count()


def get_references_to_page(page):
    """
    Get detailed references to a page using Wagtail's ReferenceIndex.

    Uses Wagtail's built-in ReferenceGroups and describe_source_field() method
    to get human-readable descriptions of references.

    Args:
        page: The Page instance to check references for.

    Returns:
        List of dicts with reference information:
            - source_title: Title of the referencing object
            - source_url: Edit URL of the referencing object (if available)
            - field_description: Human-readable description of the field path
    """
    from django.urls import reverse
    from wagtail.models import Page, ReferenceIndex

    references = []
    refs = ReferenceIndex.get_references_to(page)

    # Use Wagtail's ReferenceGroups to group references by source object
    for source_object, source_refs in refs.group_by_source_object():
        if source_object is None:
            continue

        # Get source title
        if hasattr(source_object, "title"):
            source_title = source_object.title
        elif hasattr(source_object, "__str__"):
            source_title = str(source_object)
        else:
            source_title = f"{source_object._meta.verbose_name} #{source_object.pk}"

        # Get edit URL for the source
        source_url = None
        if isinstance(source_object, Page):
            try:
                source_url = reverse("wagtailadmin_pages:edit", args=[source_object.pk])
            except Exception:
                pass

        # Get field descriptions using Wagtail's describe_source_field() method
        # Group multiple references from the same source
        field_descriptions = []
        for ref in source_refs:
            try:
                field_desc = ref.describe_source_field()
                if field_desc and field_desc not in field_descriptions:
                    field_descriptions.append(field_desc)
            except Exception:
                # Fallback to content_path if describe_source_field fails
                if ref.content_path:
                    field_descriptions.append(ref.content_path)

        references.append(
            {
                "source_title": source_title,
                "source_url": source_url,
                "field_description": ", ".join(field_descriptions)
                if field_descriptions
                else "",
            }
        )

    return references


def get_pages_for_redirect_prompt(page):
    """
    Get all pages that should be included in the redirect prompt.

    This includes:
    - The main page itself
    - All descendant pages (children, grandchildren, etc.)
    - All translations of the page (if i18n is enabled)

    Args:
        page: The Page instance being deleted/unpublished.

    Returns:
        List of dicts with page information:
            - id: Page ID
            - title: Page title
            - url: Page URL
            - references: List of detailed reference information
            - reference_count: Number of references to this page
            - group: 'main', 'children', or 'translations'
            - locale: Locale code (for translations)
    """
    pages_data = []

    # Add main page
    references = get_references_to_page(page)
    main_page_data = {
        "id": page.id,
        "title": page.title,
        "url": page.url or "/",
        "references": references,
        "reference_count": len(references),
        "group": "main",
        "locale": getattr(page, "locale", None),
    }
    pages_data.append(main_page_data)

    # Add all descendant pages
    descendants = page.get_descendants().live().specific()
    for descendant in descendants:
        desc_references = get_references_to_page(descendant)
        pages_data.append(
            {
                "id": descendant.id,
                "title": descendant.title,
                "url": descendant.url or "/",
                "references": desc_references,
                "reference_count": len(desc_references),
                "group": "children",
                "locale": getattr(descendant, "locale", None),
            }
        )

    # Add translations if i18n is enabled
    if hasattr(page, "get_translations"):
        try:
            translations = page.get_translations(inclusive=False).live()
            for trans_page in translations:
                trans_specific = trans_page.specific
                trans_references = get_references_to_page(trans_specific)
                pages_data.append(
                    {
                        "id": trans_specific.id,
                        "title": trans_specific.title,
                        "url": trans_specific.url or "/",
                        "references": trans_references,
                        "reference_count": len(trans_references),
                        "group": "translations",
                        "locale": str(getattr(trans_specific, "locale", "")),
                    }
                )
        except Exception as e:
            # i18n might not be fully configured
            logger.debug(f"Could not get translations: {e}")

    return pages_data


def pages_need_redirect_prompt(page):
    """
    Check if any pages (main page, children, or translations) have references
    that would warrant showing a redirect prompt.

    Args:
        page: The Page instance being deleted/unpublished.

    Returns:
        Boolean indicating if the redirect prompt should be shown.
    """
    pages_data = get_pages_for_redirect_prompt(page)

    # Check if any page has references
    for page_data in pages_data:
        if page_data["reference_count"] > 0:
            return True

    return False


def replace_page_references(source_page, target_page):
    """
    Replace all references to source_page with references to target_page.

    This is used when deleting a page to update all internal links and references
    to point to the redirect target, preventing broken links.

    Args:
        source_page: The Page being deleted
        target_page: The Page that references should point to instead

    Returns:
        Integer count of references updated
    """
    from wagtail.models import Page, ReferenceIndex

    updated_count = 0
    refs = ReferenceIndex.get_references_to(source_page)

    # Group references by source object to handle multiple references in one save
    objects_to_update = {}

    for source_object, source_refs in refs.group_by_source_object():
        if source_object is None:
            continue

        # Skip if the source object is the page being deleted or its descendants
        if isinstance(source_object, Page):
            if source_object.pk == source_page.pk:
                continue
            # Also skip pages that are descendants of the source page
            # (they will be deleted too)
            if source_object.is_descendant_of(source_page):
                continue

        # Collect all content paths for this object
        content_paths = []
        for ref in source_refs:
            if ref.content_path:
                content_paths.append(ref.content_path)

        if content_paths:
            objects_to_update[source_object] = content_paths

    # Update each object
    for obj, content_paths in objects_to_update.items():
        try:
            updated = _update_object_references(
                obj, source_page, target_page, content_paths
            )
            if updated:
                updated_count += 1
                logger.info(
                    f"Updated references in {obj._meta.verbose_name} "
                    f"(pk={obj.pk}) from page {source_page.pk} to {target_page.pk}"
                )
        except Exception as e:
            logger.error(
                f"Failed to update references in {obj._meta.verbose_name} "
                f"(pk={obj.pk}): {e}",
                exc_info=True,
            )

    return updated_count


def _update_object_references(obj, source_page, target_page, content_paths):
    """
    Update references within a single object from source_page to target_page.

    Args:
        obj: The object containing references
        source_page: The page being replaced
        target_page: The page to replace with
        content_paths: List of content paths where references exist

    Returns:
        Boolean indicating if the object was updated
    """
    from wagtail.fields import RichTextField, StreamField
    from wagtail.models import Page

    # If the object is a Page, get the specific subclass which has the actual fields
    if isinstance(obj, Page):
        obj = obj.specific

    updated = False

    for content_path in content_paths:
        try:
            # Parse the content path
            parts = content_path.split(".")
            field_name = parts[0]

            if not hasattr(obj, field_name):
                continue

            field = obj._meta.get_field(field_name)
            field_value = getattr(obj, field_name)

            # Handle different field types
            # Check for ForeignKey to Page
            if hasattr(field, "related_model") and field.related_model is not None:
                try:
                    if issubclass(field.related_model, Page):
                        # ForeignKey to Page
                        current_value = getattr(obj, field_name)
                        if current_value and current_value.pk == source_page.pk:
                            setattr(obj, field_name, target_page)
                            updated = True
                except (TypeError, AttributeError):
                    pass

            # Check for StreamField
            elif isinstance(field, StreamField):
                if field_value:
                    new_value = _update_streamfield_references(
                        field_value, source_page.pk, target_page.pk
                    )
                    if new_value is not None:
                        setattr(obj, field_name, new_value)
                        updated = True

            # Check for RichTextField
            elif isinstance(field, RichTextField):
                if field_value:
                    new_value = _update_richtext_references(
                        field_value, source_page.pk, target_page.pk
                    )
                    if new_value != field_value:
                        setattr(obj, field_name, new_value)
                        updated = True

        except Exception as e:
            logger.warning(f"Could not update path {content_path}: {e}", exc_info=True)

    if updated:
        # Save the object - handle Page objects specially for revision system
        if isinstance(obj, Page):
            # Save revision and publish if the page was already live
            revision = obj.save_revision()
            if obj.live:
                revision.publish()
                logger.debug(f"Published updated page: {obj.title} (pk={obj.pk})")
        else:
            obj.save()

    return updated


def _update_streamfield_references(stream_value, source_pk, target_pk):
    """
    Update page references within a StreamField value.

    This handles both:
    - PageChooserBlock references (stored as page IDs)
    - RichText blocks with page links (stored as <a linktype="page" id="X">)

    Args:
        stream_value: The StreamField value (StreamValue)
        source_pk: PK of the page to replace
        target_pk: PK of the page to replace with

    Returns:
        Updated stream data if changes were made, None otherwise
    """
    import json

    try:
        # Get the raw stream data - convert RawDataView to list if needed
        if hasattr(stream_value, "raw_data"):
            raw_data = stream_value.raw_data
            # RawDataView is not a plain list, we need to convert it
            stream_data = list(raw_data)
        elif hasattr(stream_value, "stream_data"):
            stream_data = list(stream_value.stream_data)
        else:
            return None

        # Serialize to JSON to compare before/after
        original_json = json.dumps(stream_data, sort_keys=True)

        # Replace page references - handles both page IDs and RichText links
        updated_data = _replace_page_refs_in_streamfield(
            stream_data, source_pk, target_pk
        )

        # Compare serialized versions to detect actual changes
        updated_json = json.dumps(updated_data, sort_keys=True)

        if updated_json != original_json:
            logger.debug(
                f"StreamField references updated: source_pk={source_pk} -> target_pk={target_pk}"
            )
            return updated_data

    except Exception as e:
        logger.warning(f"Could not update StreamField references: {e}", exc_info=True)

    return None


def _replace_page_refs_in_streamfield(data, source_pk, target_pk):
    """
    Recursively replace page references in StreamField data.

    Handles:
    - Page IDs in PageChooserBlock (stored as integers in 'value', 'page', etc.)
    - RichText links (stored as '<a linktype="page" id="X">')

    Args:
        data: The data structure to process
        source_pk: PK to find and replace
        target_pk: PK to replace with

    Returns:
        Updated data structure
    """
    # Common keys that hold page IDs in Wagtail StreamField data
    PAGE_ID_KEYS = (
        "page",
        "page_id",
        "link_page",
        "internal_link",
        "related_page",
        "linked_page",
        "target_page",
    )

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check if this key typically holds page IDs
            if key in PAGE_ID_KEYS:
                if value == source_pk:
                    result[key] = target_pk
                else:
                    result[key] = value
            # Check for 'value' key which could be a page ID or RichText content
            elif key == "value":
                if value == source_pk:
                    # PageChooserBlock stores page ID directly in 'value'
                    result[key] = target_pk
                elif isinstance(value, str):
                    if 'linktype="page"' in value or "linktype='page'" in value:
                        # RichText content with page links
                        result[key] = _update_richtext_references(
                            value, source_pk, target_pk
                        )
                    else:
                        result[key] = value
                else:
                    result[key] = _replace_page_refs_in_streamfield(
                        value, source_pk, target_pk
                    )
            else:
                result[key] = _replace_page_refs_in_streamfield(
                    value, source_pk, target_pk
                )
        return result
    elif isinstance(data, list):
        return [
            _replace_page_refs_in_streamfield(item, source_pk, target_pk)
            for item in data
        ]
    elif isinstance(data, str):
        # Check if this string contains RichText page links
        if 'linktype="page"' in data or "linktype='page'" in data:
            return _update_richtext_references(data, source_pk, target_pk)
        return data
    else:
        return data


def _update_richtext_references(text, source_pk, target_pk):
    """
    Update page links in RichText content.

    RichText stores page links in the format: <a linktype="page" id="123">

    Args:
        text: The RichText content (string)
        source_pk: PK of the page to replace
        target_pk: PK of the page to replace with

    Returns:
        Updated text with page references replaced
    """
    import re

    if not text:
        return text

    # Handle both RichText objects and strings
    if hasattr(text, "source"):
        text_str = text.source
    else:
        text_str = str(text)

    original = text_str

    # Simple and robust approach: find all page links and replace matching IDs
    # Pattern matches id="X" within an <a> tag that has linktype="page"

    def replace_in_tag(match):
        tag = match.group(0)
        # Check if this is a page link
        if 'linktype="page"' in tag or "linktype='page'" in tag:
            # Replace the specific page ID
            tag = re.sub(
                r'(id=["\'])' + str(source_pk) + r'(["\'])',
                r"\g<1>" + str(target_pk) + r"\g<2>",
                tag,
            )
        return tag

    # Match all <a ...> tags
    updated = re.sub(r"<a\s[^>]*>", replace_in_tag, text_str)

    if updated != original:
        logger.debug(f"RichText references updated: {source_pk} -> {target_pk}")

    return updated
