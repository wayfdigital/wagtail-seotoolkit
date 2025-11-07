"""
Wagtail SEO Toolkit Views

This module imports views from both core (MIT) and pro (Proprietary) packages
for backward compatibility with existing code.

Core views (MIT License):
- SEODashboardView, SEOIssuesReportView, RequestAuditView

Pro views (WAYF Proprietary License):
- Bulk editor, subscriptions, templates, email verification views
"""

# Core views (MIT License)
from wagtail_seotoolkit.core.views import (
    RequestAuditView,
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
    SubscriptionSettingsView,
    TemplateCreateView,
    TemplateDeleteView,
    TemplateEditView,
    TemplateListView,
    bulk_apply_metadata,
    get_placeholders_api,
    preview_metadata,
    save_as_template,
    validate_metadata_bulk,
)

__all__ = [
    # Core
    "SEODashboardView",
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
]
