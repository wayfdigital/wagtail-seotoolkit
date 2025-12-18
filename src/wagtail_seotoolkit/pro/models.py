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
