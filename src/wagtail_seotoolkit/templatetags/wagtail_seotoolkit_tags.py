"""
Custom template tags for Wagtail SEO Toolkit
"""

import logging

from django import template
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from wagtail_seotoolkit.models import SEOAuditIssueType

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def is_bulk_edit_issue(issue_type):
    """
    Check if an issue type is a bulk edit issue.

    Usage: {% if issue.issue_type|is_bulk_edit_issue %}
    """
    return SEOAuditIssueType.is_bulk_edit_issue(issue_type)


@register.filter
def get_bulk_edit_action(issue_type):
    """
    Get the bulk edit action type for an issue.

    Usage: {{ issue.issue_type|get_bulk_edit_action }}
    """
    return SEOAuditIssueType.get_bulk_edit_action_type(issue_type)


@register.simple_tag
def issue_type_filters(issue_type):
    """
    Generate URL parameters for all related issue types.

    Usage: {% issue_type_filters issue.issue_type %}
    Returns: issue_type=type1&issue_type=type2&issue_type=type3
    """
    related_types = SEOAuditIssueType.get_related_issue_types(issue_type)

    # Build query string with multiple issue_type parameters
    params = [("issue_type", issue_type) for issue_type in related_types]
    return urlencode(params)


@register.simple_tag(takes_context=True)
def jsonld_schemas(context):
    """
    Render JSON-LD schemas for the current page.

    Merges schemas with precedence: page override > page type template > site-wide.
    This is a Pro feature that requires an active subscription.

    Usage:
        {% load wagtail_seotoolkit_tags %}
        {% jsonld_schemas %}

    Place this tag in your base template's <head> section.

    Returns:
        HTML script tag containing JSON-LD structured data, or empty string if no schemas.
    """
    request = context.get("request")
    # Wagtail templates use either 'page' or 'self' for the current page
    page = context.get("page") or context.get("self")

    if not page:
        return ""

    try:
        from wagtail_seotoolkit.pro.utils.jsonld_utils import (
            generate_jsonld_for_page,
            render_jsonld_script,
        )

        schemas = generate_jsonld_for_page(page, request)
        if schemas:
            return mark_safe(render_jsonld_script(schemas))
        return ""

    except ImportError:
        # Pro features not available
        logger.warning("JSON-LD schemas require wagtail_seotoolkit Pro features")
        return ""
    except Exception as e:
        # Don't break the template if something goes wrong
        logger.error(f"Error rendering JSON-LD schemas: {e}")
        return ""
