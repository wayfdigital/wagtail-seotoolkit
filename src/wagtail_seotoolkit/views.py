"""
Views for SEO Toolkit
"""
import json

import django_filters
import requests
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.models import Locale, Page

from .models import (
    PluginEmailVerification,
    SEOAuditIssue,
    SEOAuditIssueSeverity,
    SEOAuditIssueType,
    SEOAuditRun,
    SEOMetaDescription,
    SEOTitle,
)
from .utils.placeholder_utils import process_placeholders


class SEODashboardView(TemplateView):
    """
    Main dashboard view showing SEO health score and top issues
    """

    template_name = "wagtail_seotoolkit/seo_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the latest completed audit run
        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )

        # Check for scheduled or running audits
        scheduled_audit = SEOAuditRun.objects.filter(status="scheduled").first()
        running_audit = SEOAuditRun.objects.filter(status="running").first()

        # Check if audit button should be shown
        from django.conf import settings

        show_audit_button = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_SHOW_AUDIT_BUTTON", False
        )

        context.update(
            {
                "has_scheduled_audit": scheduled_audit is not None,
                "has_running_audit": running_audit is not None,
                "scheduled_audit": scheduled_audit,
                "running_audit": running_audit,
                "show_audit_button": show_audit_button,
            }
        )

        if latest_audit:
            # Get issue counts by severity
            issues_by_severity = latest_audit.issues.values("issue_severity").annotate(
                count=Count("id")
            )

            critical_count = 0
            warnings_count = 0
            suggestions_count = 0

            for item in issues_by_severity:
                if item["issue_severity"] == SEOAuditIssueSeverity.HIGH:
                    critical_count = item["count"]
                elif item["issue_severity"] == SEOAuditIssueSeverity.MEDIUM:
                    warnings_count = item["count"]
                elif item["issue_severity"] == SEOAuditIssueSeverity.LOW:
                    suggestions_count = item["count"]

            # Get top issues by type
            top_issues = (
                latest_audit.issues.values(
                    "issue_severity", "issue_type", "requires_dev_fix"
                )
                .annotate(count=Count("id"))
                .order_by("-issue_severity", "-count")[:5]
            )

            # Format top issues with human-readable labels
            formatted_top_issues = []
            for issue in top_issues:
                # Get the display value for the issue type
                issue_type_display = dict(SEOAuditIssueType.choices).get(
                    issue["issue_type"], issue["issue_type"]
                )

                formatted_top_issues.append(
                    {
                        "type": issue_type_display,
                        "count": issue["count"],
                        "severity": issue["issue_severity"],
                        "requires_dev_fix": issue["requires_dev_fix"],
                    }
                )

            context.update(
                {
                    "latest_audit": latest_audit,
                    "health_score": latest_audit.overall_score,
                    "pages_analyzed": latest_audit.pages_analyzed,
                    "critical_count": critical_count,
                    "warnings_count": warnings_count,
                    "suggestions_count": suggestions_count,
                    "top_issues": formatted_top_issues,
                    "total_issues": critical_count + warnings_count + suggestions_count,
                }
            )
        else:
            context.update(
                {
                    "latest_audit": None,
                    "health_score": None,
                    "pages_analyzed": 0,
                    "critical_count": 0,
                    "warnings_count": 0,
                    "suggestions_count": 0,
                    "top_issues": [],
                    "total_issues": 0,
                }
            )

        # Add severity constants to context for template use
        context.update(
            {
                "SEVERITY_LOW": SEOAuditIssueSeverity.LOW,
                "SEVERITY_MEDIUM": SEOAuditIssueSeverity.MEDIUM,
                "SEVERITY_HIGH": SEOAuditIssueSeverity.HIGH,
            }
        )

        # Add stored email for verification
        verification = PluginEmailVerification.objects.first()
        context["stored_email"] = verification.email if verification else None

        return context


class SEOIssuesFilterSet(WagtailFilterSet):
    """FilterSet for SEO Issues Report"""

    issue_severity = django_filters.ChoiceFilter(
        label=_("Severity"),
        choices=[("", _("All"))] + SEOAuditIssueSeverity.choices,
        empty_label=None,
    )

    requires_dev_fix = django_filters.ChoiceFilter(
        label=_("Requires Dev Fix"),
        choices=[("", _("All")), (True, _("Yes")), (False, _("No"))],
        empty_label=None,
    )

    locale = django_filters.ModelChoiceFilter(
        label=_("Locale"),
        queryset=Locale.objects.all(),
        field_name="page__locale",
        empty_label=_("All"),
    )

    issue_type = django_filters.MultipleChoiceFilter(
        label=_("Issue Type"),
        choices=SEOAuditIssueType.choices,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = SEOAuditIssue
        fields = ["issue_severity", "locale", "requires_dev_fix", "issue_type"]


class SEOIssuesReportView(ReportView):
    """
    Report view showing all SEO issues from the latest audit
    """
    index_url_name = "seo_issues_report"
    index_results_url_name = "seo_issues_report_results"
    page_title = _("SEO Issues Report")
    header_icon = "warning"
    template_name = "wagtail_seotoolkit/seo_issues_report_base.html"
    results_template_name = "wagtail_seotoolkit/seo_issues_report.html"
    
    model = SEOAuditIssue
    filterset_class = SEOIssuesFilterSet
    
    list_export = [
        "issue_type",
        "issue_severity", 
        "page_title",
        "page_url",
        "description",
    ]
    
    def get_queryset(self):
        # Get issues from the latest completed audit run
        latest_audit = SEOAuditRun.objects.filter(status='completed').order_by('-created_at').first()
        
        if latest_audit:
            return SEOAuditIssue.objects.filter(
                audit_run=latest_audit
            ).select_related('page').order_by('-issue_severity', 'issue_type', 'page_title')
        
        return SEOAuditIssue.objects.none()
    
    def get_breadcrumbs_items(self):
        """Add SEO Dashboard to breadcrumbs"""
        from django.urls import reverse
        
        return [
            {
                "url": reverse("seo_dashboard"),
                "label": _("SEO Dashboard"),
            },
            { "url": None,
                "label": _("SEO Issues Report") },
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the latest audit for context
        latest_audit = SEOAuditRun.objects.filter(status='completed').order_by('-created_at').first()
        context['latest_audit'] = latest_audit
        
        # The object_list from parent already contains filtered results from the filterset
        # Just alias it for our template
        context['seo_issues_list'] = context.get('object_list', [])
        
        # Add severity constants to context for template use
        context.update({
            'SEVERITY_LOW': SEOAuditIssueSeverity.LOW,
            'SEVERITY_MEDIUM': SEOAuditIssueSeverity.MEDIUM,
            'SEVERITY_HIGH': SEOAuditIssueSeverity.HIGH,
        })

        # Add stored email for verification
        verification = PluginEmailVerification.objects.first()
        context["stored_email"] = verification.email if verification else None

        return context


class RequestAuditView(View):
    """
    API endpoint to request a new SEO audit.

    Creates a scheduled audit run that will be picked up by the
    run_scheduled_audits management command.
    """

    def post(self, request):
        # Check for existing scheduled or running audits
        existing_audit = SEOAuditRun.objects.filter(
            status__in=["scheduled", "running"]
        ).first()

        if existing_audit:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Audit is already {existing_audit.status}. Please wait for it to complete.",
                    "status": existing_audit.status,
                },
                status=409,
            )

        # Create new scheduled audit
        try:
            audit_run = SEOAuditRun.objects.create(
                overall_score=0, pages_analyzed=0, status="scheduled"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Audit has been scheduled successfully.",
                    "audit_id": audit_run.id,
                    "status": "scheduled",
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to schedule audit: {str(e)}"},
                status=500,
            )


class GetEmailVerificationView(View):
    """
    API endpoint to get stored email verification data.
    Returns the stored email if exists, otherwise null.
    Verification status must be checked via external API.
    """

    def get(self, request):
        try:
            verification = PluginEmailVerification.objects.first()
            if verification:
                return JsonResponse(
                    {
                        "success": True,
                        "email": verification.email,
                    }
                )
            else:
                return JsonResponse({"success": True, "email": None})
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to retrieve email: {str(e)}"},
                status=500,
            )


class SaveEmailVerificationView(View):
    """
    API endpoint to save or update email verification data.
    Only stores the email - verification status must be checked via external API.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Update or create verification record (only stores email, not verification status)
            verification, created = PluginEmailVerification.objects.get_or_create(
                email=email
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Email saved successfully",
                    "email": verification.email,
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to save email: {str(e)}"},
                status=500,
            )


class ProxySendVerificationView(View):
    """
    Proxy endpoint to send verification email via external API.
    Avoids CORS issues by making server-to-server request.
    """

    API_BASE_URL = "https://wagtail-seotoolkit-license-server.vercel.app"

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Make request to external API
            response = requests.post(
                f"{self.API_BASE_URL}/api/send-verification",
                json={"email": email},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to send verification: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error: {str(e)}"}, status=500
            )


class ProxyCheckVerifiedView(View):
    """
    Proxy endpoint to check verification status via external API.
    Avoids CORS issues by making server-to-server request.
    """

    API_BASE_URL = "https://wagtail-seotoolkit-license-server.vercel.app"

    def get(self, request):
        email = request.GET.get("email")

        if not email:
            return JsonResponse(
                {"verified": False, "pending": False, "error": "Email is required"},
                status=400,
            )

        try:
            # Make request to external API
            response = requests.get(
                f"{self.API_BASE_URL}/api/check-verified",
                params={"email": email},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "verified": False,
                    "pending": False,
                    "error": f"Failed to check verification: {str(e)}",
                },
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {"verified": False, "pending": False, "error": f"Error: {str(e)}"},
                status=500,
            )


class ProxyResendVerificationView(View):
    """
    Proxy endpoint to resend verification email via external API.
    Avoids CORS issues by making server-to-server request.
    """

    API_BASE_URL = "https://wagtail-seotoolkit-license-server.vercel.app"

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Make request to external API
            response = requests.post(
                f"{self.API_BASE_URL}/api/resend-verification",
                json={"email": email},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Failed to resend verification: {str(e)}",
                },
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error: {str(e)}"}, status=500
            )


class BulkEditFilterSet(WagtailFilterSet):
    """FilterSet for Bulk Editor"""

    issue_type = django_filters.MultipleChoiceFilter(
        label=_("Issue Type"),
        field_name="seo_issues__issue_type",
        choices=list(
            filter(
                lambda x: SEOAuditIssueType.is_bulk_edit_issue(x[0]),
                SEOAuditIssueType.choices,
            )
        ),
        widget=forms.CheckboxSelectMultiple,
    )

    content_type = django_filters.ModelMultipleChoiceFilter(
        label=_("Page Type"),
        queryset=ContentType.objects.filter(
            id__in=Page.objects.values_list("content_type_id", flat=True).distinct()
        )
        .exclude(app_label="wagtailcore")
        .order_by("app_label", "model"),
        field_name="content_type",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Page
        fields = ["locale"]


class BulkEditView(ReportView):
    """
    Bulk editor view showing all pages for SEO metadata editing
    """

    index_url_name = "bulk_edit"
    index_results_url_name = "bulk_edit_results"
    page_title = _("Bulk SEO Editor")
    header_icon = "edit"
    template_name = "wagtail_seotoolkit/bulk_edit_base.html"
    results_template_name = "wagtail_seotoolkit/bulk_edit_results.html"

    model = Page
    filterset_class = BulkEditFilterSet

    list_export = [
        "title",
        "seo_title",
        "search_description",
        "last_published_at",
    ]

    def get_queryset(self):
        # Get all pages, excluding the root page
        return (
            Page.objects.exclude(depth=1)
            .select_related("locale", "content_type")
            .prefetch_related(
                "seo_issues",
                models.Prefetch(
                    "seo_titles", queryset=SEOTitle.objects.filter(is_active=True)
                ),
                models.Prefetch(
                    "seo_meta_descriptions",
                    queryset=SEOMetaDescription.objects.filter(is_active=True),
                ),
            )
            .order_by("-last_published_at")
        )

    def get_breadcrumbs_items(self):
        """Add SEO Dashboard to breadcrumbs"""
        from django.urls import reverse

        return [
            {
                "url": reverse("seo_dashboard"),
                "label": _("SEO Dashboard"),
            },
            {
                "url": None,
                "label": _("Bulk SEO Editor"),
            },
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alias object_list for template consistency
        context["pages"] = context.get("object_list", [])

        return context


@require_POST
def preview_metadata(request):
    """
    API endpoint to preview how placeholders will be processed for selected pages.
    Returns processed values for each page to show in preview table.
    """
    try:
        page_ids = request.POST.getlist("page_ids")
        template = request.POST.get("template", "").strip()

        if not page_ids or not template:
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        previews = []
        for page in pages:
            # Get current SEO values
            current_title = SEOTitle.objects.filter(page=page, is_active=True).first()
            current_description = SEOMetaDescription.objects.filter(
                page=page, is_active=True
            ).first()

            # Process template for this page
            processed_value = process_placeholders(template, page, request)

            previews.append(
                {
                    "page_id": page.id,
                    "page_title": page.title,
                    "page_type": page.page_type_display_name,
                    "current_value": current_title.title
                    if current_title
                    else (
                        current_description.description if current_description else ""
                    ),
                    "new_value": processed_value,
                }
            )

        return JsonResponse({"success": True, "previews": previews})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def bulk_apply_metadata(request):
    """
    API endpoint to apply bulk metadata changes.
    Saves templates with placeholders - they will be processed by middleware.
    """
    try:
        page_ids = request.POST.getlist("page_ids")
        action = request.POST.get("action")
        content_template = request.POST.get("content", "").strip()

        if not page_ids or not action or not content_template:
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids)
        updated_count = 0

        for page in pages:
            # Save template as-is with placeholders
            # Middleware will process them when rendering
            if action == "edit_title":
                # Create new SEO title (automatically deactivates old ones)
                SEOTitle.objects.create(
                    page=page,
                    title=content_template[:255],  # Respect max_length
                    is_active=True,
                )
            elif action == "edit_description":
                # Create new SEO meta description (automatically deactivates old ones)
                SEOMetaDescription.objects.create(
                    page=page,
                    description=content_template[:320],  # Respect max_length
                    is_active=True,
                )
            updated_count += 1

        return JsonResponse(
            {
                "success": True,
                "updated": updated_count,
                "message": f"Successfully updated {updated_count} pages",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class BulkEditActionView(TemplateView):
    """
    View for bulk editing SEO titles or descriptions for selected pages
    """

    template_name = "wagtail_seotoolkit/bulk_edit_action.html"

    def get_available_placeholders(self, pages):
        """
        Get available field placeholders based on selected pages.
        Returns a list of dicts with field info.
        """
        from django.db.models import CharField, TextField
        from wagtail.fields import RichTextField, StreamField

        placeholders = []

        # Always include site name
        placeholders.append({"name": "site_name", "label": "Site Name", "type": "site"})

        # Always include base Page fields
        base_fields = [
            {"name": "title", "label": "Page Title", "type": "page"},
            {"name": "seo_title", "label": "SEO Title", "type": "page"},
            {
                "name": "search_description",
                "label": "Search Description",
                "type": "page",
            },
        ]
        placeholders.extend(base_fields)

        # Check if all pages are of the same specific type
        if pages:
            content_types = set(page.content_type_id for page in pages)

            if len(content_types) == 1:
                # All pages are the same type, get specific fields
                first_page = pages[0].specific
                specific_model = type(first_page)

                # Skip if it's just the base Page model
                if specific_model != Page:
                    # Get text fields from the specific model
                    for field in specific_model._meta.get_fields():
                        # Include CharField, TextField, RichTextField, and StreamField
                        if isinstance(
                            field, (CharField, TextField, RichTextField, StreamField)
                        ) and not field.name.startswith("_"):
                            # Skip fields that are already in base fields
                            if field.name not in [f["name"] for f in base_fields]:
                                # Skip internal/system fields
                                if field.name not in [
                                    "path",
                                    "url_path",
                                    "draft_title",
                                    "latest_revision_created_at",
                                ]:
                                    placeholders.append(
                                        {
                                            "name": field.name,
                                            "label": field.verbose_name.title(),
                                            "type": "specific",
                                        }
                                    )

        return placeholders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get selected page IDs from URL parameters
        page_ids = self.request.GET.getlist("page_ids")
        action = self.request.GET.get("action", "edit_title")

        # Get the selected pages with SEO data
        from django.db import models

        pages = (
            Page.objects.filter(id__in=page_ids)
            .select_related("content_type")
            .prefetch_related(
                models.Prefetch(
                    "seo_titles", queryset=SEOTitle.objects.filter(is_active=True)
                ),
                models.Prefetch(
                    "seo_meta_descriptions",
                    queryset=SEOMetaDescription.objects.filter(is_active=True),
                ),
            )
        )

        # Get available placeholders
        placeholders = self.get_available_placeholders(pages)

        context.update(
            {
                "pages": pages,
                "page_ids": page_ids,
                "action": action,
                "is_title": action == "edit_title",
                "is_description": action == "edit_description",
                "placeholders": placeholders,
            }
        )

        return context
