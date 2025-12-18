# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
SEO Metadata and JSON-LD Middleware - Pro Feature

This middleware intercepts page responses and:
1. Replaces the title tag and meta description with values from page fields
2. Injects JSON-LD structured data schemas into the page

Uses regex for performance instead of full HTML parsing.

Licensed under the WAYF Proprietary License.
"""

import logging
import re

from django.utils.deprecation import MiddlewareMixin
from wagtail.models import Page

logger = logging.getLogger(__name__)


class SEOMetadataMiddleware(MiddlewareMixin):
    """
    Middleware to process SEO metadata and JSON-LD schemas in HTML responses.

    Handles:
    - Title tag replacement with processed placeholders
    - Meta description replacement with processed placeholders
    - JSON-LD schema injection (site-wide, page type, and page-specific)
    """

    def process_response(self, request, response):
        """
        Process the response to update SEO metadata and inject JSON-LD schemas.

        Only processes placeholders if WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS is True (default).
        If False, assumes values are already processed and saved to the database.

        Args:
            request: The HTTP request
            response: The HTTP response

        Returns:
            Modified response with replaced SEO metadata and JSON-LD schemas
        """
        from django.conf import settings

        # Check if placeholder processing is enabled
        # If disabled, values are already processed and saved, so skip middleware processing
        process_placeholders_enabled = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS", True
        )

        if not process_placeholders_enabled:
            logger.debug(
                f"Skipping placeholder processing for {request.path} - disabled"
            )
            return response

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
            # Use Wagtail's built-in method to find the page for this request
            page = Page.find_for_request(request, request.path)

            if not page:
                return response

        except Exception:
            return response

        # Get page instance
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

        # Decode content
        try:
            content = response.content.decode("utf-8")
        except UnicodeDecodeError:
            # If can't decode, return unchanged
            return response

        modified = False

        # 1. Process meta tags (title and description) with placeholders
        try:
            from wagtail_seotoolkit.pro.utils.placeholder_utils import (
                process_html_with_placeholders,
            )

            processed_content = process_html_with_placeholders(
                content, page_instance, request
            )

            if processed_content != content:
                content = processed_content
                modified = True

        except Exception as e:
            logger.debug(f"Error processing meta tag placeholders: {e}")

        # 2. Inject JSON-LD schemas
        try:
            from wagtail_seotoolkit.pro.utils.jsonld_utils import (
                generate_jsonld_for_page,
                render_jsonld_script,
            )

            schemas = generate_jsonld_for_page(page_instance, request)

            if schemas:
                jsonld_html = render_jsonld_script(schemas)

                # Inject before </head> tag
                # Use case-insensitive matching for </head>
                head_close_pattern = re.compile(r"</head>", re.IGNORECASE)

                if head_close_pattern.search(content):
                    content = head_close_pattern.sub(
                        f"{jsonld_html}\n</head>", content, count=1
                    )
                    modified = True

        except Exception as e:
            logger.debug(f"Error injecting JSON-LD schemas: {e}")

        # Update response content if modified
        if modified:
            response.content = content.encode("utf-8")
            response["Content-Length"] = len(response.content)

        return response
