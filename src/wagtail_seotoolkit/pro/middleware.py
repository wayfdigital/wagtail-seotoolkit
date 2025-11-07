# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
SEO Metadata Replacement Middleware - Pro Feature

This middleware intercepts page responses and replaces the title tag and meta description
with values from the SEOTitle and SEOMetaDescription models if they exist.

Uses regex for performance instead of full HTML parsing.

Licensed under the WAYF Proprietary License.
"""

import re

from django.utils.deprecation import MiddlewareMixin
from wagtail.models import Page


class SEOMetadataMiddleware(MiddlewareMixin):
    """
    Middleware to replace title and meta description in HTML responses
    with values from SEOTitle and SEOMetaDescription models.
    """

    def process_response(self, request, response):
        """
        Process the response and replace SEO metadata if needed.

        Args:
            request: The HTTP request
            response: The HTTP response

        Returns:
            Modified response with replaced SEO metadata
        """
        # Only process HTML responses
        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type:
            return response

        # Only process successful responses
        if response.status_code != 200:
            return response

        # Skip if no content
        if not hasattr(response, "content") or not response.content:
            return response

        # Resolve the page from the URL using Wagtail's routing
        try:
            from wagtail.models import Site

            site = Site.find_for_request(request)
            if not site:
                return response

            # Get path components for routing
            path = request.path.rstrip("/")
            if not path:
                path = "/"
            path_components = [component for component in path.split("/") if component]

            # Route to the page
            page, args, kwargs = site.root_page.specific.route(request, path_components)

            if not page or not isinstance(page, Page):
                return response

        except Exception:
            return response

        # Check if we have custom SEO metadata for this page
        try:
            from wagtail_seotoolkit.pro.utils.placeholder_utils import (
                process_placeholders,
            )

            # Get SEO metadata from page fields
            # Use the latest live version if the page is live, otherwise use draft
            if page.live:
                # For live pages, use the live revision
                live_revision = page.get_latest_revision()
                if live_revision:
                    page_instance = live_revision.as_object()
                else:
                    page_instance = page
            else:
                # For draft pages, use current instance
                page_instance = page

            seo_title = page_instance.seo_title
            search_description = page_instance.search_description

            # If no custom metadata, return unchanged response
            if not seo_title and not search_description:
                return response

            # Decode content
            try:
                content = response.content.decode("utf-8")
            except UnicodeDecodeError:
                # If can't decode, return unchanged
                return response

            modified = False

            # Replace title tag if we have a custom title
            if seo_title:
                # Process placeholders in the title template
                processed_title = process_placeholders(
                    seo_title, page_instance, request
                )

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

            # Update response content if modified
            if modified:
                response.content = content.encode("utf-8")
                response["Content-Length"] = len(response.content)

        except Exception:
            # If anything goes wrong, return original response
            # We don't want middleware to break the site
            pass

        return response
