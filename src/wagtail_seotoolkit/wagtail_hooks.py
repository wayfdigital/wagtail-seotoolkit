"""
Wagtail hooks for SEO Toolkit
"""

from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .views import (
    BulkEditActionView,
    BulkEditView,
    GetEmailVerificationView,
    ProxyCheckVerifiedView,
    ProxyResendVerificationView,
    ProxySendVerificationView,
    RequestAuditView,
    SaveEmailVerificationView,
    SEODashboardView,
    SEOIssuesReportView,
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
            "api/proxy/resend-verification/",
            ProxyResendVerificationView.as_view(),
            name="proxy_resend_verification",
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
    ]


@hooks.register('register_admin_menu_item')
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
def register_templates_menu_item():
    """
    Add SEO Templates to admin menu
    """
    return MenuItem(
        _("SEO Templates"),
        reverse("seo_template_list"),
        icon_name="snippet",
        order=1002,
    )
