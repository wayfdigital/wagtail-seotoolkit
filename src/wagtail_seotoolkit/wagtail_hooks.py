"""
Wagtail hooks for SEO Toolkit
"""

from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from wagtail_seotoolkit.views import (
    BulkEditActionView,
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
    RequestAuditView,
    SaveEmailVerificationView,
    SEOAuditComparisonView,
    SEOAuditReportsListView,
    SEODashboardView,
    SEOIssuesReportView,
    SiteWideSchemaEditView,
    SubscriptionSettingsView,
    TemplateCreateView,
    TemplateDeleteView,
    TemplateEditView,
    TemplateListView,
    bulk_apply_metadata,
    get_jsonld_placeholders_api,
    get_jsonld_schema_fields_api,
    get_placeholders_api,
    preview_jsonld_api,
    preview_metadata,
    save_as_template,
    validate_metadata_bulk,
)


@hooks.register("register_admin_urls")
def register_seo_admin_urls():
    """
    Register SEO Toolkit admin URLs
    """
    return [
        path(
            "seo-dashboard/",
            SEODashboardView.as_view(),
            name="seo_dashboard",
        ),
        path(
            "seo-dashboard/request-audit/",
            RequestAuditView.as_view(),
            name="request_audit",
        ),
        path(
            "reports/seo-audits/",
            SEOAuditReportsListView.as_view(),
            name="seo_audit_reports_list",
        ),
        path(
            "reports/seo-audits/results/",
            SEOAuditReportsListView.as_view(results_only=True),
            name="seo_audit_reports_list_results",
        ),
        path(
            "seo-dashboard/comparison/",
            SEOAuditComparisonView.as_view(),
            name="seo_audit_comparison",
        ),
        path(
            "seo-dashboard/comparison/<int:report_id>/",
            SEOAuditComparisonView.as_view(),
            name="seo_audit_comparison_detail",
        ),
        path(
            "reports/seo-issues/",
            SEOIssuesReportView.as_view(),
            name="seo_issues_report",
        ),
        path(
            "reports/seo-issues/results/",
            SEOIssuesReportView.as_view(results_only=True),
            name="seo_issues_report_results",
        ),
        path(
            "seo-toolkit/bulk-edit/",
            BulkEditView.as_view(),
            name="bulk_edit",
        ),
        path(
            "seo-toolkit/bulk-edit/results/",
            BulkEditView.as_view(results_only=True),
            name="bulk_edit_results",
        ),
        path(
            "seo-toolkit/bulk-edit/action/",
            BulkEditActionView.as_view(),
            name="bulk_edit_action",
        ),
        path(
            "api/bulk-apply-metadata/",
            bulk_apply_metadata,
            name="bulk_apply_metadata",
        ),
        path(
            "api/preview-metadata/",
            preview_metadata,
            name="preview_metadata",
        ),
        path(
            "api/validate-metadata-bulk/",
            validate_metadata_bulk,
            name="validate_metadata_bulk",
        ),
        path(
            "api/email-verification/get/",
            GetEmailVerificationView.as_view(),
            name="get_email_verification",
        ),
        path(
            "api/email-verification/save/",
            SaveEmailVerificationView.as_view(),
            name="save_email_verification",
        ),
        path(
            "api/email-verification/delete/",
            DeleteEmailVerificationView.as_view(),
            name="delete_email_verification",
        ),
        path(
            "api/proxy/send-verification/",
            ProxySendVerificationView.as_view(),
            name="proxy_send_verification",
        ),
        path(
            "api/proxy/check-verified/",
            ProxyCheckVerifiedView.as_view(),
            name="proxy_check_verified",
        ),
        path(
            "api/proxy/get-dashboard-message/",
            ProxyGetDashboardMessageView.as_view(),
            name="proxy_get_dashboard_message",
        ),
        path(
            "api/proxy/resend-verification/",
            ProxyResendVerificationView.as_view(),
            name="proxy_resend_verification",
        ),
        # Subscription proxy API endpoints
        path(
            "api/proxy/get-plans/",
            ProxyGetPlansView.as_view(),
            name="proxy_get_plans",
        ),
        path(
            "api/proxy/check-subscription/",
            ProxyCheckSubscriptionView.as_view(),
            name="proxy_check_subscription",
        ),
        path(
            "api/proxy/create-checkout/",
            ProxyCreateCheckoutView.as_view(),
            name="proxy_create_checkout",
        ),
        path(
            "api/proxy/register-instance/",
            ProxyRegisterInstanceView.as_view(),
            name="proxy_register_instance",
        ),
        path(
            "api/proxy/list-instances/",
            ProxyListInstancesView.as_view(),
            name="proxy_list_instances",
        ),
        path(
            "api/proxy/remove-instance/",
            ProxyRemoveInstanceView.as_view(),
            name="proxy_remove_instance",
        ),
        path(
            "api/proxy/create-portal/",
            ProxyCreatePortalView.as_view(),
            name="proxy_create_portal",
        ),
        path(
            "api/proxy/get-active-instances/",
            ProxyGetActiveInstancesView.as_view(),
            name="proxy_get_active_instances",
        ),
        path(
            "api/proxy/set-active-instances/",
            ProxySetActiveInstancesView.as_view(),
            name="proxy_set_active_instances",
        ),
        path(
            "api/proxy/clear-active-instances/",
            ProxyClearActiveInstancesView.as_view(),
            name="proxy_clear_active_instances",
        ),
        # Subscription settings page
        path(
            "settings/subscription-settings/",
            SubscriptionSettingsView.as_view(),
            name="subscription_settings",
        ),
        path(
            "seo-toolkit/templates/",
            TemplateListView.as_view(),
            name="seo_template_list",
        ),
        path(
            "seo-toolkit/templates/create/",
            TemplateCreateView.as_view(),
            name="seo_template_create",
        ),
        path(
            "seo-toolkit/templates/<int:template_id>/edit/",
            TemplateEditView.as_view(),
            name="seo_template_edit",
        ),
        path(
            "seo-toolkit/templates/<int:template_id>/delete/",
            TemplateDeleteView.as_view(),
            name="seo_template_delete",
        ),
        path(
            "api/save-as-template/",
            save_as_template,
            name="save_as_template",
        ),
        path(
            "api/get-placeholders/",
            get_placeholders_api,
            name="get_placeholders_api",
        ),
        # JSON-LD Schema Editor URLs
        path(
            "seo-toolkit/jsonld-schemas/",
            JSONLDSchemaListView.as_view(),
            name="jsonld_schema_list",
        ),
        path(
            "seo-toolkit/jsonld-schemas/create/",
            JSONLDSchemaCreateView.as_view(),
            name="jsonld_schema_create",
        ),
        path(
            "seo-toolkit/jsonld-schemas/<int:template_id>/edit/",
            JSONLDSchemaEditView.as_view(),
            name="jsonld_schema_edit",
        ),
        path(
            "seo-toolkit/jsonld-schemas/<int:template_id>/delete/",
            JSONLDSchemaDeleteView.as_view(),
            name="jsonld_schema_delete",
        ),
        path(
            "seo-toolkit/jsonld-schemas/site-wide/",
            SiteWideSchemaEditView.as_view(),
            name="jsonld_site_wide",
        ),
        path(
            "seo-toolkit/jsonld-schemas/page/<int:page_id>/",
            PageJSONLDEditView.as_view(),
            name="jsonld_page_edit",
        ),
        path(
            "api/jsonld/schema-fields/",
            get_jsonld_schema_fields_api,
            name="jsonld_schema_fields_api",
        ),
        path(
            "api/jsonld/preview/",
            preview_jsonld_api,
            name="jsonld_preview_api",
        ),
        path(
            "api/jsonld/placeholders/",
            get_jsonld_placeholders_api,
            name="jsonld_placeholders_api",
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_seo_toolkit_menu_item():
    """
    Add SEO Toolkit menu item to Wagtail admin
    """
    return MenuItem(
        _("SEO Dashboard"),
        reverse("seo_dashboard"),
        icon_name="glasses",
        order=1000,
    )


@hooks.register("register_admin_menu_item")
def register_bulk_edit_menu_item():
    """
    Add Bulk Editor to Reports menu
    """
    return MenuItem(
        _("Bulk SEO Editor"),
        reverse("bulk_edit"),
        icon_name="edit",
        order=1001,
    )


@hooks.register("register_admin_menu_item")
def register_jsonld_editor_menu_item():
    """
    Add JSON-LD Editor to admin menu
    """
    return MenuItem(
        _("JSON-LD Editor"),
        reverse("jsonld_schema_list"),
        icon_name="code",
        order=1002,
    )


@hooks.register("register_settings_menu_item")
def register_templates_menu_item():
    """
    Add SEO Templates to settings menu
    """
    return MenuItem(
        _("SEO Templates"),
        reverse("seo_template_list"),
        icon_name="snippet",
        order=9998,
    )


@hooks.register("register_settings_menu_item")
def register_subscription_settings_menu_item():
    """
    Add Subscription Settings to Wagtail settings menu
    """
    return MenuItem(
        _("SEO Toolkit Subscription"),
        reverse("subscription_settings"),
        icon_name="lock",
        order=9999,
    )
