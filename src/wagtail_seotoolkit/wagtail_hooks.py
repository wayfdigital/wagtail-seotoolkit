"""
Wagtail hooks for SEO Toolkit
"""

from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .views import (
    GetEmailVerificationView,
    ProxyCheckVerifiedView,
    ProxyResendVerificationView,
    ProxySendVerificationView,
    RequestAuditView,
    SaveEmailVerificationView,
    SEODashboardView,
    SEOIssuesReportView,
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
