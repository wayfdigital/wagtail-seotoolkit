"""
Utilities for processing placeholders in SEO metadata templates.
"""

import re

from django.utils.html import strip_tags
from wagtail.blocks import StreamValue
from wagtail.models import Site
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

