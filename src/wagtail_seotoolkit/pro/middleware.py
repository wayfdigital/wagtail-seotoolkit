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

import logging

from django.utils.deprecation import MiddlewareMixin
from wagtail.models import Page

logger = logging.getLogger(__name__)

class SEOMetadataMiddleware(MiddlewareMixin):
    """
    Middleware to replace title and meta description in HTML responses
    with values from SEOTitle and SEOMetaDescription models.
    """

    def process_response(self, request, response):
        """
        Process the response and replace SEO metadata if needed.

        Only processes placeholders if WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS is True (default).
        If False, assumes values are already processed and saved to the database.

        Args:
            request: The HTTP request
            response: The HTTP response

        Returns:
            Modified response with replaced SEO metadata
        """
        from django.conf import settings

        # Check if placeholder processing is enabled
        # If disabled, values are already processed and saved, so skip middleware processing
        process_placeholders_enabled = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS", True
        )

        if not process_placeholders_enabled:
            logger.info(f"Skipping placeholder processing for {request.path} because it's disabled")
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

        # Check if we have custom SEO metadata for this page
        try:
            from wagtail_seotoolkit.pro.utils.placeholder_utils import (
                process_html_with_placeholders,
            )

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

            # Process HTML with placeholders
            processed_content = process_html_with_placeholders(
                content, page_instance, request
            )

            # Update response content if modified
            if processed_content != content:
                response.content = processed_content.encode("utf-8")
                response["Content-Length"] = len(response.content)

        except Exception:
            # If anything goes wrong, return original response
            # We don't want middleware to break the site
            pass

        return response
