"""
Wagtail SEO Toolkit Views

This module imports views from both core (MIT) and pro (Proprietary) packages
for backward compatibility with existing code.

Core views (MIT License):
- SEODashboardView, SEOIssuesReportView, RequestAuditView

Pro views (WAYF Proprietary License):
- Bulk editor, subscriptions, templates, email verification views
- JSON-LD schema editor views
"""

# Core views (MIT License)
from wagtail_seotoolkit.core.views import (
    RequestAuditView,
    SEOAuditComparisonView,
    SEOAuditReportsListView,
    SEODashboardView,
    SEOIssuesFilterSet,
    SEOIssuesReportView,
)

# Pro views (WAYF Proprietary License)
from wagtail_seotoolkit.pro.views import (
    BulkEditActionView,
    BulkEditFilterSet,
    BulkEditView,
    DeleteEmailVerificationView,
    GetEmailVerificationView,
    # JSON-LD Schema Editor views
    JSONLDSchemaCreateView,
    JSONLDSchemaDeleteView,
    JSONLDSchemaEditView,
    JSONLDSchemaListView,
    PageJSONLDEditView,
    ProxyCheckSubscriptionView,
    ProxyCheckVerifiedView,
    ProxyClearActiveInstancesView,
    ProxyCreateCheckoutView,
    ProxyCreatePortalView,
    ProxyGetActiveInstancesView,
    ProxyGetDashboardMessageView,
    ProxyGetPlansView,
    ProxyListInstancesView,
    ProxyRegisterInstanceView,
    ProxyRemoveInstanceView,
    ProxyResendVerificationView,
    ProxySendVerificationView,
    ProxySetActiveInstancesView,
    SaveEmailVerificationView,
    SiteWideSchemaEditView,
    SubscriptionSettingsView,
    TemplateCreateView,
    TemplateDeleteView,
    TemplateEditView,
    TemplateListView,
    bulk_apply_metadata,
    get_jsonld_placeholders_api,
    get_jsonld_schema_fields_api,
    # Target Keyword API views
    get_page_keywords_api,
    get_placeholders_api,
    preview_jsonld_api,
    preview_metadata,
    save_as_template,
    save_page_keywords_api,
    validate_metadata_bulk,
)

__all__ = [
    # Core
    "SEODashboardView",
    "SEOAuditComparisonView",
    "SEOAuditReportsListView",
    "SEOIssuesFilterSet",
    "SEOIssuesReportView",
    "RequestAuditView",
    # Pro
    "GetEmailVerificationView",
    "SaveEmailVerificationView",
    "DeleteEmailVerificationView",
    "ProxyGetDashboardMessageView",
    "ProxySendVerificationView",
    "ProxyCheckVerifiedView",
    "ProxyResendVerificationView",
    "ProxyGetPlansView",
    "ProxyCheckSubscriptionView",
    "ProxyCreateCheckoutView",
    "ProxyRegisterInstanceView",
    "ProxyListInstancesView",
    "ProxyRemoveInstanceView",
    "ProxyCreatePortalView",
    "ProxyGetActiveInstancesView",
    "ProxySetActiveInstancesView",
    "ProxyClearActiveInstancesView",
    "SubscriptionSettingsView",
    "BulkEditView",
    "BulkEditFilterSet",
    "BulkEditActionView",
    "TemplateListView",
    "TemplateCreateView",
    "TemplateEditView",
    "TemplateDeleteView",
    "preview_metadata",
    "validate_metadata_bulk",
    "bulk_apply_metadata",
    "save_as_template",
    "get_placeholders_api",
    # JSON-LD Schema Editor
    "JSONLDSchemaListView",
    "JSONLDSchemaCreateView",
    "JSONLDSchemaEditView",
    "JSONLDSchemaDeleteView",
    "SiteWideSchemaEditView",
    "PageJSONLDEditView",
    "get_jsonld_schema_fields_api",
    "preview_jsonld_api",
    "get_jsonld_placeholders_api",
    # Target Keyword API
    "get_page_keywords_api",
    "save_page_keywords_api",
]
