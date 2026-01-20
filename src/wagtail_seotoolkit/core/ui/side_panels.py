from wagtail.admin.ui.side_panels import ChecksSidePanel
from wagtail.models import Page

from wagtail_seotoolkit.models import (
    DraftSEOAudit,
    PluginEmailVerification,
    SEOAuditIssueSeverity,
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
        """
        Get SEO data for the current page from draft audit.

        Returns structured data for:
        - Content checks (title, meta, images, links) with widget data
        - Dev-required audit issues (schema, mobile, etc.)
        """
        # Get the current page
        page = self.object if issubclass(self.model, Page) else None
        if not page or not page.id:
            return None

        # Get draft audit from database
        try:
            draft_audit = (
                DraftSEOAudit.objects.select_related("page")
                .prefetch_related("issues")
                .get(page=page)
            )
        except DraftSEOAudit.DoesNotExist:
            return None

        # Get check_details for content checks widgets
        check_details = draft_audit.check_details or {}

        # Separate issues into editor-fixable and dev-required
        editor_issues = []
        dev_issues = []

        for issue in draft_audit.issues.all():
            issue_data = {
                "type": issue.get_issue_type_display(),
                "issue_type": issue.issue_type,
                "description": issue.description,
                "severity": issue.issue_severity,
                "severity_label": issue.get_issue_severity_display(),
            }

            if issue.requires_dev_fix:
                dev_issues.append(issue_data)
            else:
                editor_issues.append(issue_data)

        # Group dev issues by severity for display
        dev_critical = [i for i in dev_issues if i["severity"] == SEOAuditIssueSeverity.HIGH]
        dev_warnings = [i for i in dev_issues if i["severity"] == SEOAuditIssueSeverity.MEDIUM]
        dev_suggestions = [i for i in dev_issues if i["severity"] == SEOAuditIssueSeverity.LOW]

        return {
            "audited_at": draft_audit.audited_at,
            # Content checks data for widgets
            "title": check_details.get("title", {}),
            "meta_description": check_details.get("meta_description", {}),
            "images": check_details.get("images", []),
            "images_count": check_details.get("images_count", 0),
            "images_missing_alt": check_details.get("images_missing_alt", 0),
            "internal_links": check_details.get("internal_links", []),
            "internal_links_count": check_details.get("internal_links_count", 0),
            "min_internal_links": check_details.get("min_internal_links", 3),
            "external_links": check_details.get("external_links", []),
            "external_links_count": check_details.get("external_links_count", 0),
            # Dev-required issues
            "dev_issues": dev_issues,
            "dev_critical": dev_critical,
            "dev_warnings": dev_warnings,
            "dev_suggestions": dev_suggestions,
            "has_dev_issues": len(dev_issues) > 0,
        }

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["seo_insights"] = self.get_seo_insights()

        # Add stored email for verification
        verification = PluginEmailVerification.objects.first()
        context["stored_email"] = verification.email if verification else None

        return context
