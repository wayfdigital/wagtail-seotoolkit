# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Utilities for processing placeholders in SEO metadata templates.

Licensed under the WAYF Proprietary License.
"""

import re

from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, TextField
from django.utils.html import strip_tags
from wagtail.blocks import StreamValue
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Site
from wagtail.rich_text import RichText


def process_placeholders(template, page, request=None):
    """
    Replace placeholders in template with actual page values.
    Supports truncation syntax: {field_name[:N]}

    Args:
        template: String containing placeholders like {field_name} or {field_name[:60]}
        page: Wagtail Page object
        request: Optional Django request object (needed for site_name)

    Returns:
        String with placeholders replaced by actual values

    Examples:
        >>> process_placeholders("{title} | {site_name}", page, request)
        "About Us | Bakery Demo"

        >>> process_placeholders("{introduction[:100]}", page)
        "We are a family-owned bakery serving fresh bread since 1920..."
    """
    # Get specific page instance
    page = page.specific

    # Pattern to match {field_name} or {field_name[:N]}
    # Matches: {title} or {title[:60]}
    pattern = r"\{([^}:\[]+)(?:\[:(\d+)\])?\}"

    def replace_placeholder(match):
        field_name = match.group(1).strip()  # Remove any whitespace
        truncate_limit = match.group(2)  # e.g., "60" from [:60]

        value = ""

        # Handle special placeholders
        if field_name == "site_name":
            if request:
                site = Site.find_for_request(request)
                value = site.site_name if site else ""
            else:
                value = ""
        else:
            # Try to get field value from page
            try:
                field_value = getattr(page, field_name, None)
                if field_value is not None and field_value != "":
                    # Convert to string first
                    value = str(field_value)

                    # Check if it's a RichText, StreamField, or contains HTML tags
                    if isinstance(field_value, (RichText, StreamValue)) or "<" in value:
                        # Replace line breaks and block-level tags with spaces before stripping
                        # This ensures content from different blocks/paragraphs is separated
                        value = re.sub(
                            r"<br\s*/?>|</p>|</div>|</h[1-6]>|</li>|</td>|</tr>|</blockquote>",
                            " ",
                            value,
                            flags=re.IGNORECASE,
                        )
                        # Strip HTML tags for SEO meta tags
                        value = strip_tags(value).strip()
                        # Remove extra whitespace
                        value = " ".join(value.split())
                else:
                    # If field is empty, return empty string (not the field name)
                    value = ""
            except (AttributeError, TypeError):
                # Field doesn't exist
                value = ""

        # Apply truncation if specified
        if truncate_limit and value:
            limit = int(truncate_limit)
            value = value[:limit]

        return value

    # Use re.sub which replaces ALL occurrences
    result = re.sub(pattern, replace_placeholder, template)
    return result


def get_placeholders_for_content_type(content_type_id=None):
    """
    Get available placeholders for a given content type.

    Args:
        content_type_id: ContentType ID (None for universal placeholders)

    Returns:
        List of dicts with placeholder info: [{"name": "field", "label": "Label", "type": "type"}]
    """
    placeholders = []

    # Always include site name
    placeholders.append({"name": "site_name", "label": "Site Name", "type": "site"})

    # Always include base Page fields
    base_fields = [
        {"name": "title", "label": "Page Title", "type": "page"},
    ]
    placeholders.extend(base_fields)

    # If content_type specified, get specific fields
    if content_type_id:
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()

            # Only process if it's a Page subclass
            if model_class and issubclass(model_class, Page) and model_class != Page:
                # Get text fields from the specific model
                for field in model_class._meta.get_fields():
                    # Include CharField, TextField, RichTextField, and StreamField
                    if (
                        isinstance(
                            field, (CharField, TextField, RichTextField, StreamField)
                        )
                        and not field.name.startswith("_")
                        and field.name not in ["seo_title", "search_description"]
                    ):
                        # Skip fields that are already in base fields
                        if field.name not in [f["name"] for f in base_fields]:
                            # Skip internal/system fields
                            if field.name not in [
                                "path",
                                "url_path",
                                "draft_title",
                                "latest_revision_created_at",
                            ]:
                                placeholders.append(
                                    {
                                        "name": field.name,
                                        "label": field.verbose_name.title(),
                                        "type": "specific",
                                    }
                                )
        except (ContentType.DoesNotExist, AttributeError):
            pass

    return placeholders


def extract_placeholders_from_template(template_string):
    """
    Extract placeholder names from a template string.

    Args:
        template_string: String containing placeholders like {field_name} or {field_name[:60]}

    Returns:
        Set of placeholder field names (without truncation)

    Example:
        >>> extract_placeholders_from_template("{title[:60]} | {site_name}")
        {'title', 'site_name'}
    """
    # Pattern to match {field_name} or {field_name[:N]}
    pattern = r"\{([^}:\[]+)(?:\[:(\d+)\])?\}"
    matches = re.findall(pattern, template_string)
    # Return just the field names (first group from each match)
    return {match[0].strip() for match in matches}


def validate_template_placeholders(template_string, content_type_id=None):
    """
    Validate that all placeholders in a template are available for the content type.

    Args:
        template_string: Template string to validate
        content_type_id: ContentType ID (None for universal templates)

    Returns:
        Tuple of (is_valid, list_of_invalid_placeholders)

    Example:
        >>> validate_template_placeholders("{title} | {invalid_field}", None)
        (False, ['invalid_field'])
    """
    template_placeholders = extract_placeholders_from_template(template_string)
    available_placeholders = get_placeholders_for_content_type(content_type_id)
    available_names = {p["name"] for p in available_placeholders}

    invalid = [p for p in template_placeholders if p not in available_names]

    return (len(invalid) == 0, invalid)


def process_html_with_placeholders(html_content, page, request=None):
    """
    Process HTML content and replace SEO metadata (title and meta description) with
    values from page fields, processing any placeholders they contain.

    This function extracts the core HTML processing logic used by the middleware,
    making it reusable for SEO audits and other contexts.

    Args:
        html_content: HTML string to process
        page: Wagtail page instance (will be converted to specific if needed)
        request: Optional Django request object (needed for site_name placeholder)

    Returns:
        Processed HTML string with placeholders replaced in title and meta description

    Example:
        >>> html = '<html><head><title>Old</title></head></html>'
        >>> page.seo_title = "{title} | {site_name}"
        >>> process_html_with_placeholders(html, page, request)
        '<html><head><title>About Us | Bakery Demo</title></head></html>'
    """
    # Get specific page instance
    page_instance = page.specific if hasattr(page, 'specific') else page

    # Get SEO metadata from page fields
    seo_title = getattr(page_instance, 'seo_title', None)
    search_description = getattr(page_instance, 'search_description', None)

    # If no custom metadata, return unchanged HTML
    if not seo_title and not search_description:
        return html_content

    content = html_content
    modified = False

    # Replace title tag if we have a custom title
    if seo_title:
        # Process placeholders in the title template
        processed_title = process_placeholders(seo_title, page_instance, request)

        # Match <title>...</title> including multiline and whitespace
        title_pattern = r"<title[^>]*>.*?</title>"
        new_title = f"<title>{processed_title}</title>"

        if re.search(title_pattern, content, re.IGNORECASE | re.DOTALL):
            content = re.sub(
                title_pattern,
                new_title,
                content,
                count=1,
                flags=re.IGNORECASE | re.DOTALL,
            )
            modified = True

    # Replace meta description if we have a custom description
    if search_description:
        # Process placeholders in the description template
        processed_description = process_placeholders(
            search_description, page_instance, request
        )

        # Escape any quotes in the description for HTML attribute
        escaped_description = processed_description.replace('"', "&quot;")
        new_meta = f'<meta name="description" content="{escaped_description}">'

        # Multiple regex patterns to catch various meta description formats
        meta_patterns = [
            r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
            r"<meta\s+name='description'\s+content='[^']*'\s*/?>",
            r'<meta\s+content="[^"]*"\s+name="description"\s*/?>',
            r"<meta\s+content='[^']*'\s+name='description'\s*/?>",
            r'<meta\s+[^>]*name=["\']description["\'][^>]*>',
        ]

        meta_replaced = False
        for pattern in meta_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(
                    pattern, new_meta, content, count=1, flags=re.IGNORECASE
                )
                modified = True
                meta_replaced = True
                break

        # If no existing meta description tag found, inject after <head>
        if not meta_replaced:
            head_pattern = r"<head[^>]*>"
            if re.search(head_pattern, content, re.IGNORECASE):
                content = re.sub(
                    head_pattern,
                    lambda m: f"{m.group(0)}\n    {new_meta}",
                    content,
                    count=1,
                    flags=re.IGNORECASE,
                )
                modified = True

    return content
