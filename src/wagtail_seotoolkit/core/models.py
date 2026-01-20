"""
Core models for SEO auditing functionality.

Licensed under the MIT License. See LICENSE-MIT for details.
"""

from django.db import models

SEO_AUDIT_RUN_STATUSES = [
    ("scheduled", "Scheduled"),
    ("running", "Running"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]


class SEOAuditIssueSeverity(models.IntegerChoices):
    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"


class SEOAuditIssueType(models.TextChoices):
    # Title issues
    TITLE_MISSING = "title_missing", "Title Missing"
    TITLE_TOO_SHORT = "title_too_short", "Title Too Short"
    TITLE_TOO_LONG = "title_too_long", "Title Too Long"

    # Meta description issues
    META_DESCRIPTION_MISSING = "meta_description_missing", "Meta Description Missing"
    META_DESCRIPTION_TOO_SHORT = (
        "meta_description_too_short",
        "Meta Description Too Short",
    )
    META_DESCRIPTION_TOO_LONG = "meta_description_too_long", "Meta Description Too Long"
    META_DESCRIPTION_DUPLICATE = (
        "meta_description_duplicate",
        "Meta Description Duplicate",
    )
    META_DESCRIPTION_NO_CTA = "meta_description_no_cta", "Meta Description No CTA"

    # Content issues
    CONTENT_EMPTY = "content_empty", "Content Empty"
    CONTENT_THIN = "content_thin", "Content Thin"
    CONTENT_NO_PARAGRAPHS = "content_no_paragraphs", "Content No Paragraphs"

    # Header issues
    HEADER_NO_H1 = "header_no_h1", "Header No H1"
    HEADER_MULTIPLE_H1 = "header_multiple_h1", "Header Multiple H1"
    HEADER_NO_SUBHEADINGS = "header_no_subheadings", "Header No Subheadings"
    HEADER_BROKEN_HIERARCHY = "header_broken_hierarchy", "Header Broken Hierarchy"

    # Image issues
    IMAGE_NO_ALT = "image_no_alt", "Image No Alt Text"
    IMAGE_ALT_GENERIC = "image_alt_generic", "Image Alt Generic"
    IMAGE_ALT_TOO_LONG = "image_alt_too_long", "Image Alt Too Long"

    # Schema issues
    SCHEMA_MISSING = "schema_missing", "Schema Missing"
    SCHEMA_NO_ORGANIZATION = "schema_no_organization", "Schema No Organization/Person"
    SCHEMA_NO_ARTICLE = "schema_no_article", "Schema No Article/BlogPosting"
    SCHEMA_INVALID = "schema_invalid", "Schema Invalid"

    # Mobile issues
    MOBILE_NO_VIEWPORT = "mobile_no_viewport", "Mobile No Viewport"
    MOBILE_FIXED_WIDTH = "mobile_fixed_width", "Mobile Fixed Width"
    MOBILE_TEXT_SMALL = "mobile_text_small", "Mobile Text Small"

    # Internal linking issues
    INTERNAL_LINKS_NONE = "internal_links_none", "Internal Links None"
    INTERNAL_LINKS_FEW = "internal_links_few", "Internal Links Few"
    INTERNAL_LINKS_ALL_EXTERNAL = (
        "internal_links_all_external",
        "Internal Links All External",
    )

    # Content freshness issues
    CONTENT_NOT_UPDATED = "content_not_updated", "Content Not Updated"
    CONTENT_NO_PUBLISH_DATE = "content_no_publish_date", "Content No Publish Date"
    CONTENT_NO_MODIFIED_DATE = "content_no_modified_date", "Content No Modified Date"

    # PageSpeed Insights Performance issues
    PAGESPEED_PERFORMANCE_SCORE_LOW = (
        "pagespeed_performance_score_low",
        "PageSpeed Insights: Performance Score Low",
    )
    PAGESPEED_PERFORMANCE_SCORE_CRITICAL = (
        "pagespeed_performance_score_critical",
        "PageSpeed Insights: Performance Score Critical",
    )
    PAGESPEED_ACCESSIBILITY_SCORE_LOW = (
        "pagespeed_accessibility_score_low",
        "PageSpeed Insights: Accessibility Score Low",
    )
    PAGESPEED_ACCESSIBILITY_SCORE_CRITICAL = (
        "pagespeed_accessibility_score_critical",
        "PageSpeed Insights: Accessibility Score Critical",
    )
    PAGESPEED_BEST_PRACTICES_SCORE_LOW = (
        "pagespeed_best_practices_score_low",
        "PageSpeed Insights: Best Practices Score Low",
    )
    PAGESPEED_BEST_PRACTICES_SCORE_CRITICAL = (
        "pagespeed_best_practices_score_critical",
        "PageSpeed Insights: Best Practices Score Critical",
    )
    PAGESPEED_SEO_SCORE_LOW = (
        "pagespeed_seo_score_low",
        "PageSpeed Insights: SEO Score Low",
    )
    PAGESPEED_SEO_SCORE_CRITICAL = (
        "pagespeed_seo_score_critical",
        "PageSpeed Insights: SEO Score Critical",
    )

    # Individual Lighthouse audit failures
    PAGESPEED_LIGHTHOUSE_AUDIT_FAILED = (
        "pagespeed_lighthouse_audit_failed",
        "PageSpeed Insights: Lighthouse Audit Failed",
    )

    # Placeholder processing issues
    PLACEHOLDER_UNPROCESSED = (
        "placeholder_unprocessed",
        "Unprocessed Placeholders Detected",
    )

    @classmethod
    def get_description_template(cls, issue_type):
        """Get the description template for an issue type"""
        descriptions = {
            cls.TITLE_MISSING: "Page is missing a title tag. This is critical for SEO as title tags are the #1 on-page SEO factor.",
            cls.TITLE_TOO_SHORT: 'Title tag is too short ({length} chars). Recommended: {min_length}-{max_length} characters. Current title: "{title}"',
            cls.TITLE_TOO_LONG: "Title tag is too long ({length} chars). It may be truncated in search results. Recommended: {min_length}-{max_length} characters.",
            cls.META_DESCRIPTION_MISSING: "Page is missing a meta description. This impacts click-through rate in search results and AI Overviews context.",
            cls.META_DESCRIPTION_TOO_SHORT: "Meta description is too short ({length} chars). Recommended: {min_length}-{max_length} characters.",
            cls.META_DESCRIPTION_TOO_LONG: "Meta description is too long ({length} chars). It may be truncated in search results. Recommended: {min_length}-{max_length} characters.",
            cls.META_DESCRIPTION_NO_CTA: "Meta description lacks call-to-action words (e.g., {cta_examples}). Adding CTAs can improve click-through rates.",
            cls.CONTENT_EMPTY: "Page has no {content_type} content. Empty pages rarely rank in search results.",
            cls.CONTENT_THIN: "Page has thin content ({word_count} words). Recommended: at least {min_words} words. AI Overviews favor comprehensive content.",
            cls.CONTENT_NO_PARAGRAPHS: "Content lacks paragraph structure. Breaking content into paragraphs improves readability and user experience.",
            cls.HEADER_NO_H1: "Page is missing an H1 tag. H1 tags are critical for SEO and help search engines understand page content.",
            cls.HEADER_MULTIPLE_H1: "Page has {count} H1 tags. Best practice is to have exactly one H1 per page.",
            cls.HEADER_NO_SUBHEADINGS: "Page has {word_count} words but no H2 or H3 subheadings. Headers help structure content for users and search engines.",
            cls.HEADER_BROKEN_HIERARCHY: "Header hierarchy is broken: found {current} after {previous}. Headers should follow sequential order (H1→H2→H3).",
            cls.IMAGE_NO_ALT: "{count} image(s) are missing alt text. Alt text is critical for accessibility and helps images rank in Google Images.",
            cls.IMAGE_ALT_GENERIC: 'Image has generic alt text: "{alt_text}". Alt text should be descriptive and meaningful.',
            cls.IMAGE_ALT_TOO_LONG: "Image alt text is too long ({length} chars). Recommended: under {max_length} characters.",
            cls.SCHEMA_MISSING: "Page has no Schema markup (JSON-LD). AI Overviews and Google rely on structured data to understand content.",
            cls.SCHEMA_NO_ORGANIZATION: "Page is missing Organization/Person schema. This helps establish entity relationships and trust signals.",
            cls.SCHEMA_NO_ARTICLE: "Content page is missing Article/BlogPosting schema. This helps with rich results and AI Overview citations.",
            cls.SCHEMA_INVALID: "Page has invalid JSON-LD structured data. Fix syntax errors to ensure search engines can parse your schema.",
            cls.MOBILE_NO_VIEWPORT: 'Page is missing viewport meta tag. This is essential for mobile-first indexing. Add: <meta name="viewport" content="width=device-width, initial-scale=1">',
            cls.MOBILE_FIXED_WIDTH: "Page appears to use fixed-width layout. Use responsive design with relative units (%, em, rem) for better mobile experience.",
            cls.INTERNAL_LINKS_NONE: "Page has no internal links. Internal linking is critical for topical authority and helping users navigate your site.",
            cls.INTERNAL_LINKS_FEW: "Content page has only {count} internal link(s). Recommended: at least {min_links} internal links for better site structure.",
            cls.INTERNAL_LINKS_ALL_EXTERNAL: "Page has {external_count} external links but no internal links. Internal links help Google understand site structure.",
            cls.CONTENT_NOT_UPDATED: "Content was published {days_old} days ago and may need updating. Google favors fresh content for time-sensitive queries.",
            cls.CONTENT_NO_PUBLISH_DATE: "Content page is missing published date metadata. Add article:published_time meta tag or datePublished in schema.",
            cls.CONTENT_NO_MODIFIED_DATE: "Content page is missing last modified date. Add article:modified_time meta tag or dateModified in schema for time-sensitive content.",
            # PageSpeed Insights issues
            cls.PAGESPEED_PERFORMANCE_SCORE_LOW: "Performance score is {score}/100. Consider optimizing images, reducing JavaScript, and improving server response times.",
            cls.PAGESPEED_PERFORMANCE_SCORE_CRITICAL: "Performance score is critically low ({score}/100). This significantly impacts user experience and SEO rankings.",
            cls.PAGESPEED_ACCESSIBILITY_SCORE_LOW: "Accessibility score is {score}/100. Improve keyboard navigation, color contrast, and screen reader compatibility.",
            cls.PAGESPEED_ACCESSIBILITY_SCORE_CRITICAL: "Accessibility score is critically low ({score}/100). This creates barriers for users with disabilities.",
            cls.PAGESPEED_BEST_PRACTICES_SCORE_LOW: "Best practices score is {score}/100. Address security vulnerabilities, deprecated APIs, and modern web standards.",
            cls.PAGESPEED_BEST_PRACTICES_SCORE_CRITICAL: "Best practices score is critically low ({score}/100). Critical security or compatibility issues detected.",
            cls.PAGESPEED_SEO_SCORE_LOW: "SEO score is {score}/100. Improve meta tags, structured data, and content optimization.",
            cls.PAGESPEED_SEO_SCORE_CRITICAL: "SEO score is critically low ({score}/100). Major SEO issues affecting search visibility.",
            cls.PAGESPEED_LIGHTHOUSE_AUDIT_FAILED: "Lighthouse audit failed: {audit_title}. {audit_description}",
            # Placeholder processing issues
            cls.PLACEHOLDER_UNPROCESSED: "SEO metadata contains unprocessed placeholders ({placeholders}). Middleware processing is disabled. Re-apply templates in bulk editor to process placeholders.",
        }
        return descriptions.get(issue_type, "")

    @classmethod
    def requires_dev_fix(cls, issue_type):
        """Check if an issue type requires developer attention"""
        dev_required_issues = {
            cls.SCHEMA_MISSING,
            cls.SCHEMA_NO_ORGANIZATION,
            cls.SCHEMA_NO_ARTICLE,
            cls.SCHEMA_INVALID,
            cls.MOBILE_NO_VIEWPORT,
            cls.MOBILE_FIXED_WIDTH,
            cls.MOBILE_TEXT_SMALL,
            cls.CONTENT_NO_PUBLISH_DATE,
            cls.CONTENT_NO_MODIFIED_DATE,
            # PageSpeed Insights issues require dev fixes
            cls.PAGESPEED_PERFORMANCE_SCORE_LOW,
            cls.PAGESPEED_PERFORMANCE_SCORE_CRITICAL,
            cls.PAGESPEED_ACCESSIBILITY_SCORE_LOW,
            cls.PAGESPEED_ACCESSIBILITY_SCORE_CRITICAL,
            cls.PAGESPEED_BEST_PRACTICES_SCORE_LOW,
            cls.PAGESPEED_BEST_PRACTICES_SCORE_CRITICAL,
            cls.PAGESPEED_SEO_SCORE_LOW,
            cls.PAGESPEED_SEO_SCORE_CRITICAL,
            cls.PAGESPEED_LIGHTHOUSE_AUDIT_FAILED,
        }
        return issue_type in dev_required_issues

    @classmethod
    def get_severity(cls, issue_type):
        """Get the severity level for an issue type"""
        severity_mapping = {
            # Title issues
            cls.TITLE_MISSING: SEOAuditIssueSeverity.HIGH,
            cls.TITLE_TOO_SHORT: SEOAuditIssueSeverity.MEDIUM,
            cls.TITLE_TOO_LONG: SEOAuditIssueSeverity.MEDIUM,
            # Meta description issues
            cls.META_DESCRIPTION_MISSING: SEOAuditIssueSeverity.MEDIUM,
            cls.META_DESCRIPTION_TOO_SHORT: SEOAuditIssueSeverity.MEDIUM,
            cls.META_DESCRIPTION_TOO_LONG: SEOAuditIssueSeverity.MEDIUM,
            cls.META_DESCRIPTION_DUPLICATE: SEOAuditIssueSeverity.LOW,
            cls.META_DESCRIPTION_NO_CTA: SEOAuditIssueSeverity.LOW,
            # Content issues
            cls.CONTENT_EMPTY: SEOAuditIssueSeverity.HIGH,
            cls.CONTENT_THIN: SEOAuditIssueSeverity.MEDIUM,
            cls.CONTENT_NO_PARAGRAPHS: SEOAuditIssueSeverity.LOW,
            # Header issues
            cls.HEADER_NO_H1: SEOAuditIssueSeverity.HIGH,
            cls.HEADER_MULTIPLE_H1: SEOAuditIssueSeverity.MEDIUM,
            cls.HEADER_NO_SUBHEADINGS: SEOAuditIssueSeverity.MEDIUM,
            cls.HEADER_BROKEN_HIERARCHY: SEOAuditIssueSeverity.MEDIUM,
            # Image issues
            cls.IMAGE_NO_ALT: SEOAuditIssueSeverity.MEDIUM,
            cls.IMAGE_ALT_GENERIC: SEOAuditIssueSeverity.LOW,
            cls.IMAGE_ALT_TOO_LONG: SEOAuditIssueSeverity.LOW,
            # Schema issues
            cls.SCHEMA_MISSING: SEOAuditIssueSeverity.HIGH,
            cls.SCHEMA_NO_ORGANIZATION: SEOAuditIssueSeverity.MEDIUM,
            cls.SCHEMA_NO_ARTICLE: SEOAuditIssueSeverity.MEDIUM,
            cls.SCHEMA_INVALID: SEOAuditIssueSeverity.HIGH,
            # Mobile issues
            cls.MOBILE_NO_VIEWPORT: SEOAuditIssueSeverity.HIGH,
            cls.MOBILE_FIXED_WIDTH: SEOAuditIssueSeverity.MEDIUM,
            cls.MOBILE_TEXT_SMALL: SEOAuditIssueSeverity.MEDIUM,
            # Internal linking issues
            cls.INTERNAL_LINKS_NONE: SEOAuditIssueSeverity.MEDIUM,
            cls.INTERNAL_LINKS_FEW: SEOAuditIssueSeverity.LOW,
            cls.INTERNAL_LINKS_ALL_EXTERNAL: SEOAuditIssueSeverity.LOW,
            # Content freshness issues
            cls.CONTENT_NOT_UPDATED: SEOAuditIssueSeverity.LOW,
            cls.CONTENT_NO_PUBLISH_DATE: SEOAuditIssueSeverity.LOW,
            cls.CONTENT_NO_MODIFIED_DATE: SEOAuditIssueSeverity.LOW,
            # PageSpeed Insights issues
            cls.PAGESPEED_PERFORMANCE_SCORE_LOW: SEOAuditIssueSeverity.MEDIUM,
            cls.PAGESPEED_PERFORMANCE_SCORE_CRITICAL: SEOAuditIssueSeverity.HIGH,
            cls.PAGESPEED_ACCESSIBILITY_SCORE_LOW: SEOAuditIssueSeverity.MEDIUM,
            cls.PAGESPEED_ACCESSIBILITY_SCORE_CRITICAL: SEOAuditIssueSeverity.HIGH,
            cls.PAGESPEED_BEST_PRACTICES_SCORE_LOW: SEOAuditIssueSeverity.MEDIUM,
            cls.PAGESPEED_BEST_PRACTICES_SCORE_CRITICAL: SEOAuditIssueSeverity.HIGH,
            cls.PAGESPEED_SEO_SCORE_LOW: SEOAuditIssueSeverity.MEDIUM,
            cls.PAGESPEED_SEO_SCORE_CRITICAL: SEOAuditIssueSeverity.HIGH,
            cls.PAGESPEED_LIGHTHOUSE_AUDIT_FAILED: SEOAuditIssueSeverity.MEDIUM,
            # Placeholder processing issues
            cls.PLACEHOLDER_UNPROCESSED: SEOAuditIssueSeverity.HIGH,
        }
        return severity_mapping.get(issue_type, SEOAuditIssueSeverity.MEDIUM)

    @classmethod
    def is_bulk_edit_issue(cls, issue_type):
        """Check if an issue type is a bulk edit issue"""
        bulk_edit_issues = {
            cls.TITLE_MISSING,
            cls.TITLE_TOO_SHORT,
            cls.TITLE_TOO_LONG,
            cls.META_DESCRIPTION_MISSING,
            cls.META_DESCRIPTION_TOO_SHORT,
            cls.META_DESCRIPTION_TOO_LONG,
            cls.META_DESCRIPTION_DUPLICATE,
            cls.META_DESCRIPTION_NO_CTA,
            cls.PLACEHOLDER_UNPROCESSED,
        }
        return issue_type in bulk_edit_issues

    @classmethod
    def get_bulk_edit_action_type(cls, issue_type):
        """Get the bulk edit action type for an issue (edit_title or edit_description)"""
        title_issues = {
            cls.TITLE_MISSING,
            cls.TITLE_TOO_SHORT,
            cls.TITLE_TOO_LONG,
        }
        meta_issues = {
            cls.META_DESCRIPTION_MISSING,
            cls.META_DESCRIPTION_TOO_SHORT,
            cls.META_DESCRIPTION_TOO_LONG,
            cls.META_DESCRIPTION_DUPLICATE,
            cls.META_DESCRIPTION_NO_CTA,
        }

        if issue_type in title_issues:
            return "edit_title"
        elif issue_type in meta_issues:
            return "edit_description"
        return None

    @classmethod
    def get_related_issue_types(cls, issue_type):
        """Get all related issue types for a given issue type (e.g., all title issues)"""
        title_issues = [
            cls.TITLE_MISSING,
            cls.TITLE_TOO_SHORT,
            cls.TITLE_TOO_LONG,
        ]
        meta_issues = [
            cls.META_DESCRIPTION_MISSING,
            cls.META_DESCRIPTION_TOO_SHORT,
            cls.META_DESCRIPTION_TOO_LONG,
            cls.META_DESCRIPTION_DUPLICATE,
            cls.META_DESCRIPTION_NO_CTA,
        ]

        if issue_type in title_issues:
            return title_issues
        elif issue_type in meta_issues:
            return meta_issues
        return []


class SEOAuditRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, choices=SEO_AUDIT_RUN_STATUSES)
    overall_score = models.IntegerField()
    pages_analyzed = models.IntegerField()

    def __str__(self):
        return self.status


class SEOAuditIssue(models.Model):
    audit_run = models.ForeignKey(
        SEOAuditRun, on_delete=models.CASCADE, related_name="issues"
    )
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seo_issues",
        help_text="The page this issue relates to",
    )
    issue_type = models.CharField(max_length=255, choices=SEOAuditIssueType.choices)
    issue_severity = models.IntegerField(choices=SEOAuditIssueSeverity.choices)
    page_url = models.CharField(max_length=512, blank=True)
    page_title = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)
    requires_dev_fix = models.BooleanField(
        default=False,
        help_text="Whether this issue requires developer attention and cannot be fixed by content editors",
    )

    class Meta:
        ordering = ["-issue_severity", "issue_type"]

    def __str__(self):
        return f"{self.get_issue_type_display()} - {self.get_issue_severity_display()}"


class SEOAuditReport(models.Model):
    """
    Historical comparison report between two audit runs.

    Generated when the configured reporting interval is met.
    Contains aggregated metrics and flags for email notification status.
    """

    current_audit = models.ForeignKey(
        SEOAuditRun,
        on_delete=models.CASCADE,
        related_name="reports_as_current",
        help_text="The more recent audit run",
    )
    previous_audit = models.ForeignKey(
        SEOAuditRun,
        on_delete=models.CASCADE,
        related_name="reports_as_previous",
        help_text="The older audit run being compared against",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Aggregated metrics
    score_change = models.IntegerField(
        help_text="Change in overall score (can be negative)"
    )
    new_issues_count = models.IntegerField(
        default=0, help_text="Total number of new issues in current audit"
    )
    fixed_issues_count = models.IntegerField(
        default=0, help_text="Total number of issues fixed since previous audit"
    )
    new_issues_old_pages_count = models.IntegerField(
        default=0, help_text="New issues on pages that existed in previous audit"
    )
    new_issues_new_pages_count = models.IntegerField(
        default=0, help_text="New issues on pages created after previous audit"
    )

    # Email notification tracking
    email_sent = models.BooleanField(
        default=False, help_text="Whether email notification was sent for this report"
    )
    email_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When the email notification was sent"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report: {self.previous_audit.created_at.strftime('%Y-%m-%d')} → {self.current_audit.created_at.strftime('%Y-%m-%d')}"


class DraftSEOAudit(models.Model):
    """
    Draft audit metadata for a single page.

    Stores the score, timestamp, and detailed check data for the latest draft audit.
    Only one draft audit per page is kept - older ones are deleted when a new one is saved.

    The check_details JSONField stores structured data for UI widgets:
    {
        "title": {"present": bool, "value": str, "length": int, "min_length": int, "max_length": int, "status": str},
        "meta_description": {"present": bool, "value": str, "length": int, "min_length": int, "max_length": int, "status": str},
        "images": [{"src": str, "alt": str, "has_alt": bool}],
        "internal_links": [{"href": str, "text": str}],
        "internal_links_count": int,
        "min_internal_links": int,
        "external_links": [{"href": str, "text": str}]
    }
    """

    page = models.OneToOneField(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="draft_seo_audit",
        help_text="The page this draft audit relates to",
    )
    score = models.IntegerField(help_text="SEO score for this draft (0-100)")
    audited_at = models.DateTimeField(
        auto_now=True, help_text="When this draft was last audited"
    )
    check_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed check data for UI widgets (title, meta, images, links)",
    )

    class Meta:
        indexes = [
            models.Index(fields=["page", "audited_at"]),
        ]

    def __str__(self):
        return f"Draft Audit: {self.page.title} (Score: {self.score})"


class DraftSEOAuditIssue(models.Model):
    """
    Individual SEO issues found in page drafts.

    Related to a DraftSEOAudit which stores the overall score and metadata.
    Issues are deleted when their parent DraftSEOAudit is deleted.
    """

    draft_audit = models.ForeignKey(
        DraftSEOAudit,
        on_delete=models.CASCADE,
        related_name="issues",
        help_text="The draft audit this issue belongs to",
    )
    issue_type = models.CharField(max_length=255, choices=SEOAuditIssueType.choices)
    issue_severity = models.IntegerField(choices=SEOAuditIssueSeverity.choices)
    description = models.TextField(blank=True)
    requires_dev_fix = models.BooleanField(
        default=False, help_text="Whether this issue requires developer attention"
    )

    class Meta:
        ordering = ["-issue_severity", "issue_type"]

    def __str__(self):
        return f"Draft: {self.get_issue_type_display()} - {self.draft_audit.page.title}"
