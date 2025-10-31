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
    SEOMetadataTemplate,
)
from .utils.placeholder_utils import (
    get_placeholders_for_content_type,
    process_placeholders,
    validate_template_placeholders,
)


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
                issue_type_value = issue["issue_type"]
                issue_type_display = dict(SEOAuditIssueType.choices).get(
                    issue_type_value, issue_type_value
                )

                # Check if this is a bulk edit issue and get action type
                is_bulk_editable = SEOAuditIssueType.is_bulk_edit_issue(
                    issue_type_value
                )
                bulk_edit_action = SEOAuditIssueType.get_bulk_edit_action_type(
                    issue_type_value
                )
                related_types = SEOAuditIssueType.get_related_issue_types(
                    issue_type_value
                )

                formatted_top_issues.append(
                    {
                        "type": issue_type_display,
                        "type_value": issue_type_value,
                        "count": issue["count"],
                        "severity": issue["issue_severity"],
                        "requires_dev_fix": issue["requires_dev_fix"],
                        "is_bulk_editable": is_bulk_editable,
                        "bulk_edit_action": bulk_edit_action,
                        "related_types": related_types,
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
        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )

        if latest_audit:
            return (
                SEOAuditIssue.objects.filter(audit_run=latest_audit)
                .select_related("page")
                .order_by("-issue_severity", "issue_type", "page_title")
            )

        return SEOAuditIssue.objects.none()

    def get_breadcrumbs_items(self):
        """Add SEO Dashboard to breadcrumbs"""
        from django.urls import reverse

        return [
            {
                "url": reverse("seo_dashboard"),
                "label": _("SEO Dashboard"),
            },
            {"url": None, "label": _("SEO Issues Report")},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the latest audit for context
        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )
        context["latest_audit"] = latest_audit

        # The object_list from parent already contains filtered results from the filterset
        # Just alias it for our template
        context["seo_issues_list"] = context.get("object_list", [])

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
            .prefetch_related("seo_issues")
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
        action = request.POST.get("action", "edit_title")

        if not page_ids or not template:
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        previews = []
        for page in pages:
            # Get the latest revision to show current values
            latest_revision = page.get_latest_revision()
            if latest_revision:
                page_instance = latest_revision.as_object()
            else:
                page_instance = page.specific

            # Get current SEO values from page fields
            if action == "edit_title":
                current_value_raw = page_instance.seo_title or ""
            else:  # edit_description
                current_value_raw = page_instance.search_description or ""

            # Process placeholders in current value
            current_value = (
                process_placeholders(current_value_raw, page_instance, request)
                if current_value_raw
                else ""
            )

            # Process template for this page
            processed_value = process_placeholders(template, page_instance, request)

            previews.append(
                {
                    "page_id": page.id,
                    "page_title": page.title,
                    "page_type": page.page_type_display_name,
                    "current_value": current_value,
                    "new_value": processed_value,
                }
            )

        return JsonResponse({"success": True, "previews": previews})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def validate_metadata_bulk(request):
    """
    API endpoint to validate SEO metadata for multiple pages.

    Validates either titles or meta descriptions based on action parameter,
    and returns validation results for each page including issues and severity.

    Expected POST data:
        - page_ids: List of page IDs
        - template: Template string with placeholders
        - action: Either "edit_title" or "edit_description"

    Returns:
        JSON with validation results for each page
    """
    try:
        from .utils.seo_validators import validate_meta_description, validate_title

        page_ids = request.POST.getlist("page_ids")
        template = request.POST.get("template", "").strip()
        action = request.POST.get("action", "edit_title")

        if not page_ids:
            return JsonResponse(
                {"success": False, "error": "Missing page_ids parameter"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        validations = []
        for page in pages:
            # Get the latest revision
            latest_revision = page.get_latest_revision()
            if latest_revision:
                page_instance = latest_revision.as_object()
            else:
                page_instance = page.specific

            # Process template to get the actual value
            if template:
                processed_value = process_placeholders(template, page_instance, request)
            else:
                # If no template, use current value
                if action == "edit_title":
                    processed_value = page_instance.seo_title or ""
                else:  # edit_description
                    processed_value = page_instance.search_description or ""

            # Validate based on action type
            if action == "edit_title":
                validation_result = validate_title(processed_value)
            else:  # edit_description
                validation_result = validate_meta_description(processed_value)

            validations.append(
                {
                    "page_id": page.id,
                    "page_title": page.title,
                    "value": processed_value,
                    **validation_result,
                }
            )

        return JsonResponse({"success": True, "validations": validations})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def bulk_apply_metadata(request):
    """
    API endpoint to apply bulk metadata changes.
    Saves templates with placeholders to page fields via revisions.
    Automatically publishes revisions for live pages without unpublished changes.
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

        # Track which pages to publish (must check BEFORE creating revisions)
        pages_to_publish = []
        pages_to_leave_draft = []

        for page in pages:
            # Check if page should be auto-published
            # Must check has_unpublished_changes BEFORE creating revision
            should_publish = page.live and not page.has_unpublished_changes

            # Get the latest revision to base our changes on
            latest_revision = page.get_latest_revision()
            if latest_revision:
                page_instance = latest_revision.as_object()
            else:
                page_instance = page.specific

            # Update the appropriate field with template (containing placeholders)
            if action == "edit_title":
                page_instance.seo_title = content_template[:255]  # Respect max_length
            elif action == "edit_description":
                page_instance.search_description = content_template[
                    :320
                ]  # Respect max_length

            # Save as a new revision with proper log entry
            new_revision = page_instance.save_revision(
                user=request.user if request.user.is_authenticated else None,
                log_action=True,  # Create log entry for revision history
                changed=True,  # Mark that content has changed
            )

            # Publish if appropriate
            if should_publish:
                # Publish the revision with proper log action
                new_revision.publish(
                    user=request.user if request.user.is_authenticated else None,
                    log_action=True,  # Create log entry for publish action
                )
                pages_to_publish.append(
                    {
                        "id": page.id,
                        "title": page.title,
                    }
                )
            else:
                pages_to_leave_draft.append(
                    {
                        "id": page.id,
                        "title": page.title,
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "updated": len(pages),
                "published": len(pages_to_publish),
                "draft": len(pages_to_leave_draft),
                "published_pages": pages_to_publish,
                "draft_pages": pages_to_leave_draft,
                "message": f"Successfully updated {len(pages)} pages ({len(pages_to_publish)} published, {len(pages_to_leave_draft)} left as draft)",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateListView(TemplateView):
    """
    View for listing all SEO metadata templates
    """

    template_name = "wagtail_seotoolkit/template_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        templates = SEOMetadataTemplate.objects.all().select_related(
            "created_by", "content_type"
        )

        context.update(
            {
                "templates": templates,
                "page_title": _("SEO Metadata Templates"),
            }
        )

        return context


class TemplateCreateView(TemplateView):
    """
    View for creating a new SEO metadata template
    """

    template_name = "wagtail_seotoolkit/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available content types (page types)
        page_content_types = (
            ContentType.objects.filter(
                id__in=Page.objects.values_list("content_type_id", flat=True).distinct()
            )
            .exclude(app_label="wagtailcore")
            .order_by("app_label", "model")
        )

        # Get initial placeholders (for "All Page Types")
        initial_placeholders = get_placeholders_for_content_type(None)

        context.update(
            {
                "page_title": _("Create SEO Template"),
                "is_create": True,
                "template_types": SEOMetadataTemplate.TEMPLATE_TYPE_CHOICES,
                "page_content_types": page_content_types,
                "placeholders": initial_placeholders,
            }
        )

        return context

    def post(self, request):
        """Handle template creation"""
        try:
            name = request.POST.get("name", "").strip()
            template_type = request.POST.get("template_type", "title")
            template_content = request.POST.get("template_content", "").strip()
            content_type_id = request.POST.get("content_type", "").strip()

            if not name:
                return JsonResponse(
                    {"success": False, "error": "Template name is required"}, status=400
                )

            if not template_content:
                return JsonResponse(
                    {"success": False, "error": "Template content is required"},
                    status=400,
                )

            # Get content type if specified
            content_type = None
            content_type_id_int = None
            if content_type_id:
                try:
                    content_type = ContentType.objects.get(id=content_type_id)
                    content_type_id_int = int(content_type_id)
                except ContentType.DoesNotExist:
                    pass

            # Validate placeholders
            is_valid, invalid_placeholders = validate_template_placeholders(
                template_content, content_type_id_int
            )

            if not is_valid:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Invalid placeholders detected: {', '.join(invalid_placeholders)}. "
                        f"These fields are not available for the selected page type.",
                    },
                    status=400,
                )

            template = SEOMetadataTemplate.objects.create(
                name=name,
                template_type=template_type,
                template_content=template_content,
                content_type=content_type,
                created_by=request.user if request.user.is_authenticated else None,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Template created successfully",
                    "template_id": template.id,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateEditView(TemplateView):
    """
    View for editing an existing SEO metadata template
    """

    template_name = "wagtail_seotoolkit/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        template_id = kwargs.get("template_id")
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)

            # Get available content types (page types)
            page_content_types = (
                ContentType.objects.filter(
                    id__in=Page.objects.values_list(
                        "content_type_id", flat=True
                    ).distinct()
                )
                .exclude(app_label="wagtailcore")
                .order_by("app_label", "model")
            )

            # Get placeholders for current content type
            placeholders = get_placeholders_for_content_type(
                template.content_type_id if template.content_type else None
            )

            context.update(
                {
                    "page_title": _("Edit SEO Template"),
                    "is_create": False,
                    "template": template,
                    "template_types": SEOMetadataTemplate.TEMPLATE_TYPE_CHOICES,
                    "page_content_types": page_content_types,
                    "placeholders": placeholders,
                }
            )
        except SEOMetadataTemplate.DoesNotExist:
            context.update({"error": "Template not found"})

        return context

    def post(self, request, template_id):
        """Handle template update"""
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)

            name = request.POST.get("name", "").strip()
            template_type = request.POST.get("template_type", "title")
            template_content = request.POST.get("template_content", "").strip()
            content_type_id = request.POST.get("content_type", "").strip()

            if not name:
                return JsonResponse(
                    {"success": False, "error": "Template name is required"}, status=400
                )

            if not template_content:
                return JsonResponse(
                    {"success": False, "error": "Template content is required"},
                    status=400,
                )

            # Get content type if specified
            content_type = None
            content_type_id_int = None
            if content_type_id:
                try:
                    content_type = ContentType.objects.get(id=content_type_id)
                    content_type_id_int = int(content_type_id)
                except ContentType.DoesNotExist:
                    pass

            # Validate placeholders
            is_valid, invalid_placeholders = validate_template_placeholders(
                template_content, content_type_id_int
            )

            if not is_valid:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Invalid placeholders detected: {', '.join(invalid_placeholders)}. "
                        f"These fields are not available for the selected page type.",
                    },
                    status=400,
                )

            template.name = name
            template.template_type = template_type
            template.template_content = template_content
            template.content_type = content_type
            template.save()

            return JsonResponse(
                {"success": True, "message": "Template updated successfully"}
            )

        except SEOMetadataTemplate.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Template not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateDeleteView(View):
    """
    View for deleting an SEO metadata template
    """

    def post(self, request, template_id):
        """Handle template deletion"""
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)
            template_name = template.name
            template.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Template "{template_name}" deleted successfully',
                }
            )

        except SEOMetadataTemplate.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Template not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


def get_placeholders_api(request):
    """
    API endpoint to get available placeholders for a content type.
    Returns JSON list of placeholder objects.
    """
    content_type_id = request.GET.get("content_type_id")

    try:
        # Convert to int if provided
        if content_type_id:
            content_type_id = int(content_type_id)
        else:
            content_type_id = None

        placeholders = get_placeholders_for_content_type(content_type_id)

        return JsonResponse({"success": True, "placeholders": placeholders})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def save_as_template(request):
    """
    API endpoint to save current bulk edit content as a new template
    """
    try:
        name = request.POST.get("name", "").strip()
        template_type = request.POST.get("template_type", "title")
        template_content = request.POST.get("template_content", "").strip()
        content_type_id = request.POST.get("content_type_id", "").strip()

        if not name:
            return JsonResponse(
                {"success": False, "error": "Template name is required"}, status=400
            )

        if not template_content:
            return JsonResponse(
                {"success": False, "error": "Template content is required"}, status=400
            )

        # Get content type if specified
        content_type = None
        if content_type_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
            except ContentType.DoesNotExist:
                pass

        # Check if template with same name exists
        existing = SEOMetadataTemplate.objects.filter(
            name=name, template_type=template_type
        ).first()

        if existing:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"A {template_type} template with name '{name}' already exists",
                },
                status=400,
            )

        template = SEOMetadataTemplate.objects.create(
            name=name,
            template_type=template_type,
            template_content=template_content,
            content_type=content_type,
            created_by=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Template '{name}' saved successfully",
                "template_id": template.id,
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
        # Get content types of selected pages
        content_types = set(page.content_type_id for page in pages) if pages else set()

        # If all pages are the same type, get placeholders for that type
        if len(content_types) == 1:
            content_type_id = list(content_types)[0]
            return get_placeholders_for_content_type(content_type_id)
        else:
            # Mixed or no pages - return universal placeholders
            return get_placeholders_for_content_type(None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get selected page IDs from URL parameters
        page_ids = self.request.GET.getlist("page_ids")
        action = self.request.GET.get("action", "edit_title")

        # Get the selected pages
        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        # Process current values with placeholders
        pages_with_processed = []
        for page in pages:
            page_instance = page.specific

            # Get current value and process placeholders
            if action == "edit_title":
                current_raw = page_instance.seo_title or ""
            else:  # edit_description
                current_raw = page_instance.search_description or ""

            # Process placeholders in current value
            current_processed = (
                process_placeholders(current_raw, page_instance, self.request)
                if current_raw
                else ""
            )

            # Add processed value to page object
            page.current_processed = current_processed
            pages_with_processed.append(page)

        # Get available placeholders
        placeholders = self.get_available_placeholders(pages)

        # Determine template type based on action
        template_type = "title" if action == "edit_title" else "description"

        # Get content types of selected pages
        selected_content_types = set(page.content_type_id for page in pages)

        # Get templates: those with no content_type (all pages) or matching content_type
        # Only show templates if all selected pages are of the same type
        templates = (
            SEOMetadataTemplate.objects.filter(template_type=template_type)
            .filter(
                models.Q(content_type__isnull=True)
                | models.Q(content_type_id__in=selected_content_types)
            )
            .select_related("content_type")
        )

        # If multiple content types selected, only show "all pages" templates
        if len(selected_content_types) > 1:
            templates = templates.filter(content_type__isnull=True)

        # Get the content_type_id for save template feature
        content_type_id = None
        if len(selected_content_types) == 1:
            content_type_id = list(selected_content_types)[0]

        context.update(
            {
                "pages": pages_with_processed,
                "page_ids": page_ids,
                "action": action,
                "is_title": action == "edit_title",
                "is_description": action == "edit_description",
                "placeholders": placeholders,
                "templates": templates,
                "content_type_id": content_type_id,
                "template_type": template_type,
            }
        )

        return context
