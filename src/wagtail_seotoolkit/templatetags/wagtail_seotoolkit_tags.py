"""
Custom template tags for Wagtail SEO Toolkit
"""

from django import template
from django.utils.http import urlencode

from wagtail_seotoolkit.models import SEOAuditIssueType

register = template.Library()


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
