"""
Core views for SEO audit dashboard and reporting.

Licensed under the MIT License. See LICENSE-MIT for details.
"""

import django_filters
from django import forms
from django.db.models import Count
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.models import Locale

from wagtail_seotoolkit.core.models import (
    SEOAuditIssue,
    SEOAuditIssueSeverity,
    SEOAuditIssueType,
    SEOAuditReport,
    SEOAuditRun,
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

        # Try to add stored email for verification (Pro feature)
        try:
            from wagtail_seotoolkit.pro.models import PluginEmailVerification

            verification = PluginEmailVerification.objects.first()
            context["stored_email"] = verification.email if verification else None
        except ImportError:
            context["stored_email"] = None

        # Add historical report data
        import json

        from wagtail_seotoolkit.core.models import SEOAuditReport

        latest_report = SEOAuditReport.objects.order_by("-created_at").first()

        # Get historical audit runs for chart (last 15 completed audits)
        audit_runs = SEOAuditRun.objects.filter(status="completed").order_by(
            "-created_at"
        )[:15]

        # Build chart data (reverse to show oldest to newest)
        chart_data = {
            "labels": [],
            "scores": [],
        }

        if audit_runs:
            for audit in reversed(audit_runs):
                chart_data["labels"].append(audit.created_at.strftime("%b %d, %Y"))
                chart_data["scores"].append(audit.overall_score)

        # Format the reporting interval for display
        from django.conf import settings as django_settings

        from wagtail_seotoolkit.core.utils.reporting import parse_interval

        interval_str = getattr(
            django_settings, "WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL", "7d"
        )

        try:
            interval = parse_interval(interval_str)
            # Format interval nicely
            days = interval.days
            if days == 1:
                interval_display = "daily"
            elif days == 7:
                interval_display = "weekly"
            elif days == 14:
                interval_display = "every 2 weeks"
            elif days == 30 or days == 31:
                interval_display = "monthly"
            elif days % 7 == 0:
                weeks = days // 7
                interval_display = f"every {weeks} weeks"
            else:
                interval_display = f"every {days} days"
        except ValueError:
            interval_display = "periodic"

        if latest_report:
            # Determine trend indicator
            if latest_report.score_change > 0:
                score_trend = "up"
            elif latest_report.score_change < 0:
                score_trend = "down"
            else:
                score_trend = "same"

            context.update(
                {
                    "latest_report": latest_report,
                    "score_trend": score_trend,
                    "has_historical_data": True,
                    "chart_data_json": json.dumps(chart_data),
                    "report_interval": interval_display,
                }
            )
        else:
            context.update(
                {
                    "latest_report": None,
                    "score_trend": None,
                    "has_historical_data": False,
                    "chart_data_json": json.dumps(chart_data),
                    "report_interval": interval_display,
                }
            )

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

        # Try to add stored email for verification (Pro feature)
        try:
            from wagtail_seotoolkit.pro.models import PluginEmailVerification

            verification = PluginEmailVerification.objects.first()
            context["stored_email"] = verification.email if verification else None
        except ImportError:
            context["stored_email"] = None

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


class SEOAuditReportsListView(ReportView):
    """
    Report view showing all historical comparison reports with pagination.

    Displays a chronological archive of all generated audit comparison reports
    using Wagtail's built-in ReportView for pagination and filtering.
    """

    index_url_name = "seo_audit_reports_list"
    index_results_url_name = "seo_audit_reports_list_results"
    page_title = _("Historical Reports")
    header_icon = "doc-full-inverse"
    template_name = "wagtail_seotoolkit/seo_audit_reports_base.html"
    results_template_name = "wagtail_seotoolkit/seo_audit_reports_results.html"

    model = SEOAuditReport
    paginate_by = 20

    list_export = [
        "created_at",
        "previous_audit__created_at",
        "current_audit__created_at",
        "score_change",
        "new_issues_count",
        "fixed_issues_count",
    ]

    def get_queryset(self):
        from wagtail_seotoolkit.core.models import SEOAuditReport

        return SEOAuditReport.objects.select_related(
            "current_audit", "previous_audit"
        ).order_by("-created_at")

    def get_breadcrumbs_items(self):
        """Add SEO Dashboard to breadcrumbs"""
        from django.urls import reverse

        return [
            {
                "url": reverse("seo_dashboard"),
                "label": _("SEO Dashboard"),
            },
            {"url": None, "label": _("Historical Reports")},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alias object_list for template
        context["reports"] = context.get("object_list", [])

        return context


class SEOAuditComparisonView(TemplateView):
    """
    Detailed comparison view showing changes between two audit runs.

    Displays comprehensive comparison including score changes, new issues,
    fixed issues, and breakdowns by page type.
    """

    template_name = "wagtail_seotoolkit/seo_audit_comparison.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from wagtail_seotoolkit.core.models import SEOAuditReport
        from wagtail_seotoolkit.core.utils.reporting import generate_report_data

        # Get report ID from URL parameter, or use latest report
        report_id = kwargs.get("report_id", None)

        if report_id:
            report = SEOAuditReport.objects.filter(id=report_id).first()
        else:
            report = SEOAuditReport.objects.order_by("-created_at").first()

        if not report:
            context.update(
                {
                    "report": None,
                    "has_report": False,
                }
            )
            return context

        # Generate detailed report data
        detailed_data = generate_report_data(
            report.previous_audit, report.current_audit
        )

        # Determine score trend
        if report.score_change > 0:
            score_trend = "up"
        elif report.score_change < 0:
            score_trend = "down"
        else:
            score_trend = "same"

        # Get top new issues (limit to 10)
        top_new_issues = (
            detailed_data["all_new_issues"]
            .select_related("page")
            .order_by("-issue_severity", "issue_type")[:10]
        )

        # Get top fixed issues (limit to 10)
        top_fixed_issues = (
            detailed_data["all_fixed_issues"]
            .select_related("page")
            .order_by("-issue_severity", "issue_type")[:10]
        )

        # Get new issues for old pages (limit to 10)
        new_issues_old_pages = (
            detailed_data["new_issues_old_pages"]
            .select_related("page")
            .order_by("-issue_severity", "issue_type")[:10]
        )

        # Get new issues for new pages (limit to 10)
        new_issues_new_pages = (
            detailed_data["new_issues_new_pages"]
            .select_related("page")
            .order_by("-issue_severity", "issue_type")[:10]
        )

        # Get issue counts by severity for both audits
        previous_issues_by_severity = report.previous_audit.issues.values(
            "issue_severity"
        ).annotate(count=Count("id"))
        current_issues_by_severity = report.current_audit.issues.values(
            "issue_severity"
        ).annotate(count=Count("id"))

        # Convert to dictionaries for easy access
        prev_severity_counts = {
            item["issue_severity"]: item["count"]
            for item in previous_issues_by_severity
        }
        curr_severity_counts = {
            item["issue_severity"]: item["count"] for item in current_issues_by_severity
        }

        context.update(
            {
                "report": report,
                "has_report": True,
                "score_trend": score_trend,
                "top_new_issues": top_new_issues,
                "top_fixed_issues": top_fixed_issues,
                "new_issues_old_pages": new_issues_old_pages,
                "new_issues_new_pages": new_issues_new_pages,
                "prev_high_count": prev_severity_counts.get(
                    SEOAuditIssueSeverity.HIGH, 0
                ),
                "prev_medium_count": prev_severity_counts.get(
                    SEOAuditIssueSeverity.MEDIUM, 0
                ),
                "prev_low_count": prev_severity_counts.get(
                    SEOAuditIssueSeverity.LOW, 0
                ),
                "curr_high_count": curr_severity_counts.get(
                    SEOAuditIssueSeverity.HIGH, 0
                ),
                "curr_medium_count": curr_severity_counts.get(
                    SEOAuditIssueSeverity.MEDIUM, 0
                ),
                "curr_low_count": curr_severity_counts.get(
                    SEOAuditIssueSeverity.LOW, 0
                ),
                "SEVERITY_LOW": SEOAuditIssueSeverity.LOW,
                "SEVERITY_MEDIUM": SEOAuditIssueSeverity.MEDIUM,
                "SEVERITY_HIGH": SEOAuditIssueSeverity.HIGH,
            }
        )

        return context
