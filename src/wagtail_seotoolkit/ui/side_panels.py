from django.utils.translation import gettext_lazy
from wagtail.admin.ui.side_panels import BaseSidePanel
from wagtail.admin.userbar import AccessibilityItem, apply_userbar_hooks
from wagtail.models import Page

from wagtail_seotoolkit.models import SEOAuditIssue, SEOAuditIssueSeverity, SEOAuditRun


class CustomChecksSidePanel(BaseSidePanel):
    class SidePanelToggle(BaseSidePanel.SidePanelToggle):
        aria_label = gettext_lazy("Toggle checks")
        icon_name = "glasses"

    name = "checks"
    title = gettext_lazy("Checks")
    template_name = "wagtail_seotoolkit/checks_sidepanel.html"
    order = 350

    class Media:
        css = {
            "all": ["wagtail_seotoolkit/css/checks_sidepanel.css"]
        }

    def get_axe_configuration(self):
        # Retrieve the Axe configuration from the userbar.
        userbar_items = [AccessibilityItem(in_editor=True)]
        page = self.object if issubclass(self.model, Page) else None
        apply_userbar_hooks(self.request, userbar_items, page)

        for item in userbar_items:
            if isinstance(item, AccessibilityItem):
                return item.get_axe_configuration(self.request)

    def get_seo_insights(self):
        """Get SEO issues for the current page from the latest audit"""
        
        # Get the current page
        page = self.object if issubclass(self.model, Page) else None
        if not page or not page.id:
            return None
        
        # Get the latest completed audit
        latest_audit = SEOAuditRun.objects.filter(status='completed').order_by('-created_at').first()
        if not latest_audit:
            return None
        
        # Get issues for this page
        issues = SEOAuditIssue.objects.filter(
            audit_run=latest_audit,
            page=page
        ).order_by('-issue_severity', 'issue_type')
        
        # Group issues by severity
        critical_issues = []
        warning_issues = []
        suggestion_issues = []
        
        for issue in issues:
            issue_data = {
                'type': issue.get_issue_type_display(),
                'description': issue.description,
            }
            
            if issue.issue_severity == SEOAuditIssueSeverity.HIGH:
                critical_issues.append(issue_data)
            elif issue.issue_severity == SEOAuditIssueSeverity.MEDIUM:
                warning_issues.append(issue_data)
            else:
                suggestion_issues.append(issue_data)
        
        return {
            'latest_audit': latest_audit,
            'total_issues': issues.count(),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'suggestion_issues': suggestion_issues,
        }

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["axe_configuration"] = self.get_axe_configuration()
        context["seo_insights"] = self.get_seo_insights()
        return context
