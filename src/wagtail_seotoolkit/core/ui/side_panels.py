from wagtail.admin.ui.side_panels import ChecksSidePanel
from wagtail.models import Page

from wagtail_seotoolkit.models import (
    PluginEmailVerification,
    SEOAuditIssue,
    SEOAuditIssueSeverity,
    SEOAuditRun,
)


class CustomChecksSidePanel(ChecksSidePanel):
    template_name = "wagtail_seotoolkit/checks_sidepanel.html"

    class Media:
        css = {
            "all": [
                "wagtail_seotoolkit/css/checks_sidepanel.css",
                "wagtail_seotoolkit/css/dev_badge.css",
            ]
        }

    def get_seo_insights(self):
        """Get SEO issues for the current page from the latest audit"""

        # Get the current page
        page = self.object if issubclass(self.model, Page) else None
        if not page or not page.id:
            return None

        # Get the latest completed audit
        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )
        if not latest_audit:
            return None

        # Get issues for this page
        issues = SEOAuditIssue.objects.filter(
            audit_run=latest_audit, page=page
        ).order_by("-issue_severity", "issue_type")

        # Group issues by severity
        critical_issues = []
        warning_issues = []
        suggestion_issues = []

        for issue in issues:
            issue_data = {
                "type": issue.get_issue_type_display(),
                "description": issue.description,
                "requires_dev_fix": issue.requires_dev_fix,
            }

            if issue.issue_severity == SEOAuditIssueSeverity.HIGH:
                critical_issues.append(issue_data)
            elif issue.issue_severity == SEOAuditIssueSeverity.MEDIUM:
                warning_issues.append(issue_data)
            else:
                suggestion_issues.append(issue_data)

        return {
            "latest_audit": latest_audit,
            "total_issues": issues.count(),
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "suggestion_issues": suggestion_issues,
        }

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["seo_insights"] = self.get_seo_insights()

        # Add stored email for verification
        verification = PluginEmailVerification.objects.first()
        context["stored_email"] = verification.email if verification else None

        return context
