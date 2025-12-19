"""
Wagtail SEO Toolkit Models

This module imports models from both core (MIT) and pro (Proprietary) packages
for backward compatibility with existing code.

Core models (MIT License):
- SEOAuditRun, SEOAuditIssue, SEOAuditIssueSeverity, SEOAuditIssueType

Pro models (WAYF Proprietary License):
- PluginEmailVerification, SubscriptionLicense, SEOMetadataTemplate
- JSONLDSchemaTemplate, SiteWideJSONLDSchema, PageJSONLDOverride
"""

# Core models (MIT License)
from wagtail_seotoolkit.core.models import (
    SEO_AUDIT_RUN_STATUSES,
    SEOAuditIssue,
    SEOAuditIssueSeverity,
    SEOAuditIssueType,
    SEOAuditRun,
)

# Pro models (WAYF Proprietary License)
from wagtail_seotoolkit.pro.models import (
    BrokenLinkAuditResult,
    JSONLDSchemaTemplate,
    PageJSONLDOverride,
    PluginEmailVerification,
    RedirectAuditResult,
    SEOMetadataTemplate,
    SiteWideJSONLDSchema,
    SubscriptionLicense,
)

__all__ = [
    # Core
    "SEO_AUDIT_RUN_STATUSES",
    "SEOAuditRun",
    "SEOAuditIssue",
    "SEOAuditIssueSeverity",
    "SEOAuditIssueType",
    # Pro
    "PluginEmailVerification",
    "SubscriptionLicense",
    "SEOMetadataTemplate",
    "RedirectAuditResult",
    "BrokenLinkAuditResult",
    # JSON-LD Schema Editor
    "JSONLDSchemaTemplate",
    "SiteWideJSONLDSchema",
    "PageJSONLDOverride",
]
