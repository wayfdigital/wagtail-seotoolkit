# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Pro models for subscription management and SEO templates.

Licensed under the WAYF Proprietary License.
"""

import uuid

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

from wagtail_seotoolkit.pro.blocks.jsonld_blocks import (
    JSONLDSchemaFieldsBlock,
    JSONLDSchemasBlock,
    SiteWideSchemasBlock,
)


class PluginEmailVerification(models.Model):
    """
    Stores email for plugin license verification.
    This is a singleton model - only one record should exist.
    Verification status is always checked via external API to prevent local manipulation.
    """

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plugin Email Verification"
        verbose_name_plural = "Plugin Email Verifications"

    def __str__(self):
        return self.email


class SubscriptionLicense(models.Model):
    """
    Stores ONLY instance_id for this Wagtail instance.
    Email is synced from PluginEmailVerification (single source of truth).
    Subscription status is ALWAYS checked via external API (never stored locally).
    This prevents local tampering - follows PluginEmailVerification pattern.
    """

    instance_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription License"
        verbose_name_plural = "Subscription Licenses"

    @property
    def email(self):
        """Get email from PluginEmailVerification (single source of truth)"""
        verification = PluginEmailVerification.objects.first()
        return verification.email if verification else None

    def __str__(self):
        email = self.email or "No email configured"
        return f"{email} - {self.instance_id}"


class SEOMetadataTemplate(models.Model):
    """
    Stores reusable templates for SEO titles and meta descriptions.
    Templates can contain placeholders like {title}, {site_name}, etc.
    Templates can be page-type specific or apply to all pages.
    """

    TEMPLATE_TYPE_CHOICES = [
        ("title", "SEO Title"),
        ("description", "Meta Description"),
    ]

    name = models.CharField(
        max_length=100,
        help_text="A descriptive name for this template (e.g., 'Blog Post Title', 'Product Description')",
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        help_text="Whether this template is for titles or descriptions",
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Leave blank for a template that works with all page types, or select a specific page type",
    )
    template_content = models.TextField(
        max_length=320,
        help_text="Template content. Use placeholders like {title}, {site_name}, etc. Add [:N] to truncate.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seo_templates",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SEO Metadata Template"
        verbose_name_plural = "SEO Metadata Templates"

    def __str__(self):
        content_type_str = (
            f" - {self.content_type.name}" if self.content_type else " - All Pages"
        )
        return f"{self.name} ({self.get_template_type_display()}){content_type_str}"

    def clean(self):
        """Validate template content"""
        from django.core.exceptions import ValidationError

        if not self.template_content:
            raise ValidationError({"template_content": "Template content is required."})


class JSONLDSchemaTemplate(models.Model):
    """
    Page-type specific JSON-LD schema templates using StreamField.
    One template per page type (content_type).
    Templates can contain multiple schema blocks (BlogPosting, Article, etc.).
    Supports placeholders like {title}, {author_name} for dynamic values.
    """

    name = models.CharField(
        max_length=100,
        help_text="A descriptive name for this template (e.g., 'Blog Post Schemas')",
    )
    content_type = models.OneToOneField(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Select a page type. Leave blank for a default template for all page types.",
        related_name="jsonld_template",
    )
    schemas = StreamField(
        JSONLDSchemasBlock(),
        use_json_field=True,
        blank=True,
        help_text="Add schema types (BlogPosting, Article, etc.) and configure their fields.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template should be applied to pages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jsonld_templates",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("content_type"),
        FieldPanel("schemas"),
        FieldPanel("is_active"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "JSON-LD Schema Template"
        verbose_name_plural = "JSON-LD Schema Templates"

    def __str__(self):
        content_type_str = (
            f" - {self.content_type.name}" if self.content_type else " - All Pages"
        )
        return f"{self.name}{content_type_str}"


class SiteWideJSONLDSchema(models.Model):
    """
    Site-wide JSON-LD schemas for a Wagtail site.
    One schema record per site, containing multiple schema types via StreamField.
    Base name/URL are auto-populated from Wagtail Site settings.
    """

    site = models.OneToOneField(
        "wagtailcore.Site",
        on_delete=models.CASCADE,
        related_name="jsonld_schema",
        help_text="The Wagtail site this schema belongs to",
    )
    schemas = StreamField(
        SiteWideSchemasBlock(),
        use_json_field=True,
        blank=True,
        help_text="Add site-wide schemas (Organization, WebSite, LocalBusiness). Name and URL are auto-populated from Site settings.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether site-wide schemas should be included on pages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("site"),
        FieldPanel("schemas"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = "Site-Wide JSON-LD Schema"
        verbose_name_plural = "Site-Wide JSON-LD Schemas"

    def __str__(self):
        return f"{self.site.site_name} - Site-Wide Schemas"


class PageJSONLDOverride(models.Model):
    """
    Per-page JSON-LD schema overrides.
    Allows customizing or replacing the template-generated schemas for specific pages.
    When use_template is True, schemas are merged with template (override takes precedence).
    """

    page = models.OneToOneField(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="jsonld_override",
        help_text="The page this override applies to",
    )
    schemas = StreamField(
        JSONLDSchemasBlock(),
        use_json_field=True,
        blank=True,
        help_text="Add schema types and configure their fields. These override template values.",
    )
    use_template = models.BooleanField(
        default=True,
        help_text="If enabled, merge with page type template. If disabled, use only these schemas.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this override should be applied",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("page"),
        FieldPanel("use_template"),
        FieldPanel("schemas"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = "Page JSON-LD Override"
        verbose_name_plural = "Page JSON-LD Overrides"

    def __str__(self):
        return f"{self.page.title} - JSON-LD Override"


class RedirectAuditResult(models.Model):
    """
    Stores redirect audit results linked to an SEO audit run.

    Captures metrics about redirect health including chains, loops, and 404 targets.
    The audit_details JSONField stores detailed information about problematic redirects.
    """

    audit_run = models.OneToOneField(
        "wagtail_seotoolkit.SEOAuditRun",
        on_delete=models.CASCADE,
        related_name="redirect_audit",
        help_text="The SEO audit run this redirect audit belongs to",
    )
    total_redirects = models.IntegerField(
        default=0,
        help_text="Total number of redirects in the system",
    )
    chains_detected = models.IntegerField(
        default=0,
        help_text="Number of redirect chains longer than 1 hop",
    )
    circular_loops = models.IntegerField(
        default=0,
        help_text="Number of circular redirect loops detected",
    )
    redirects_to_404 = models.IntegerField(
        default=0,
        help_text="Number of redirects pointing to 404/deleted pages",
    )
    redirects_to_unpublished = models.IntegerField(
        default=0,
        help_text="Number of redirects pointing to unpublished pages",
    )
    external_redirects = models.IntegerField(
        default=0,
        help_text="Number of redirects to external URLs",
    )
    chains_flattened = models.IntegerField(
        default=0,
        help_text="Number of redirect chains flattened during this audit",
    )
    audit_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed information about problematic redirects (chains, loops, 404s)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Redirect Audit Result"
        verbose_name_plural = "Redirect Audit Results"

    def __str__(self):
        return (
            f"Redirect Audit - {self.audit_run.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    @property
    def has_issues(self):
        """Check if there are any redirect issues."""
        return (
            self.chains_detected > 0
            or self.circular_loops > 0
            or self.redirects_to_404 > 0
            or self.redirects_to_unpublished > 0
        )

    @property
    def health_score(self):
        """
        Calculate a health score for redirects (0-100).
        100 = no issues, lower scores indicate more problems.
        """
        if self.total_redirects == 0:
            return 100

        # Calculate penalty based on issues
        issue_count = (
            self.chains_detected
            + (self.circular_loops * 3)  # Loops are more serious
            + (self.redirects_to_404 * 2)  # 404s are serious
            + self.redirects_to_unpublished
        )

        # Calculate percentage of problematic redirects
        penalty = min(100, (issue_count / self.total_redirects) * 100)
        return max(0, int(100 - penalty))


class BrokenLinkAuditResult(models.Model):
    """
    Stores broken link audit results linked to an SEO audit run.

    Captures metrics about broken links found in page content,
    including internal links to deleted/unpublished pages and external broken links.
    """

    audit_run = models.OneToOneField(
        "wagtail_seotoolkit.SEOAuditRun",
        on_delete=models.CASCADE,
        related_name="broken_link_audit",
        help_text="The SEO audit run this broken link audit belongs to",
    )
    total_pages_scanned = models.IntegerField(
        default=0,
        help_text="Total number of pages scanned for broken links",
    )
    total_links_checked = models.IntegerField(
        default=0,
        help_text="Total number of links checked",
    )
    broken_internal_links = models.IntegerField(
        default=0,
        help_text="Number of internal links pointing to deleted pages",
    )
    links_to_unpublished = models.IntegerField(
        default=0,
        help_text="Number of internal links pointing to unpublished pages",
    )
    broken_external_links = models.IntegerField(
        default=0,
        help_text="Number of external links that return errors",
    )
    audit_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed information about broken links found",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Broken Link Audit Result"
        verbose_name_plural = "Broken Link Audit Results"

    def __str__(self):
        return f"Broken Link Audit - {self.audit_run.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def total_broken(self):
        """Total number of broken links found."""
        return (
            self.broken_internal_links
            + self.links_to_unpublished
            + self.broken_external_links
        )

    @property
    def has_issues(self):
        """Check if there are any broken link issues."""
        return self.total_broken > 0

    @property
    def health_score(self):
        """
        Calculate a health score for links (0-100).
        100 = no issues, lower scores indicate more problems.
        """
        if self.total_links_checked == 0:
            return 100

        # Calculate penalty based on issues
        issue_count = (
            (self.broken_internal_links * 3)  # Deleted pages are serious
            + (self.links_to_unpublished * 2)  # Unpublished is moderate
            + self.broken_external_links  # External is less critical
        )

        # Calculate percentage of problematic links
        penalty = min(100, (issue_count / max(1, self.total_links_checked)) * 100)
        return max(0, int(100 - penalty))
