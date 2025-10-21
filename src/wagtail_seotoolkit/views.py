"""
Views for SEO Toolkit
"""
import django_filters
from django.db.models import Count
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView

from .models import (
    SEOAuditIssue,
    SEOAuditIssueSeverity,
    SEOAuditIssueType,
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
        latest_audit = SEOAuditRun.objects.filter(status='completed').order_by('-created_at').first()
        
        # Check for scheduled or running audits
        scheduled_audit = SEOAuditRun.objects.filter(status='scheduled').first()
        running_audit = SEOAuditRun.objects.filter(status='running').first()
        
        context.update({
            'has_scheduled_audit': scheduled_audit is not None,
            'has_running_audit': running_audit is not None,
            'scheduled_audit': scheduled_audit,
            'running_audit': running_audit,
        })
        
        if latest_audit:
            # Get issue counts by severity
            issues_by_severity = latest_audit.issues.values('issue_severity').annotate(
                count=Count('id')
            )
            
            critical_count = 0
            warnings_count = 0
            suggestions_count = 0
            
            for item in issues_by_severity:
                if item['issue_severity'] == SEOAuditIssueSeverity.HIGH:
                    critical_count = item['count']
                elif item['issue_severity'] == SEOAuditIssueSeverity.MEDIUM:
                    warnings_count = item['count']
                elif item['issue_severity'] == SEOAuditIssueSeverity.LOW:
                    suggestions_count = item['count']
            
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
            
            context.update({
                'latest_audit': latest_audit,
                'health_score': latest_audit.overall_score,
                'pages_analyzed': latest_audit.pages_analyzed,
                'critical_count': critical_count,
                'warnings_count': warnings_count,
                'suggestions_count': suggestions_count,
                'top_issues': formatted_top_issues,
                'total_issues': critical_count + warnings_count + suggestions_count,
            })
        else:
            context.update({
                'latest_audit': None,
                'health_score': None,
                'pages_analyzed': 0,
                'critical_count': 0,
                'warnings_count': 0,
                'suggestions_count': 0,
                'top_issues': [],
                'total_issues': 0,
            })
        
        # Add severity constants to context for template use
        context.update({
            'SEVERITY_LOW': SEOAuditIssueSeverity.LOW,
            'SEVERITY_MEDIUM': SEOAuditIssueSeverity.MEDIUM,
            'SEVERITY_HIGH': SEOAuditIssueSeverity.HIGH,
        })

        return context

class SEOIssuesFilterSet(WagtailFilterSet):
    """FilterSet for SEO Issues Report"""
    
    issue_severity = django_filters.ChoiceFilter(
        label=_("Severity"),
        choices=[('', _('All'))] + SEOAuditIssueSeverity.choices,
        empty_label=None,
    )
    
    class Meta:
        model = SEOAuditIssue
        fields = ['issue_severity']


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
            status__in=['scheduled', 'running']
        ).first()
        
        if existing_audit:
            return JsonResponse({
                'success': False,
                'error': f'Audit is already {existing_audit.status}. Please wait for it to complete.',
                'status': existing_audit.status
            }, status=409)
        
        # Create new scheduled audit
        try:
            audit_run = SEOAuditRun.objects.create(
                overall_score=0,
                pages_analyzed=0,
                status='scheduled'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Audit has been scheduled successfully.',
                'audit_id': audit_run.id,
                'status': 'scheduled'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to schedule audit: {str(e)}'
            }, status=500)

