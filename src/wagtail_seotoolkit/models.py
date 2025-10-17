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
        }
        return descriptions.get(issue_type, "")


class SEOAuditRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, choices=SEO_AUDIT_RUN_STATUSES)
    overall_score = models.IntegerField()
    pages_analyzed = models.IntegerField()

    def __str__(self):
        return self.status


class SEOAuditIssue(models.Model):
    audit_run = models.ForeignKey(SEOAuditRun, on_delete=models.CASCADE, related_name='issues')
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
    
    class Meta:
        ordering = ['-issue_severity', 'issue_type']

    def __str__(self):
        return f"{self.get_issue_type_display()} - {self.get_issue_severity_display()}"
