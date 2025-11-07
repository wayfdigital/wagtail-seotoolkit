# Generated migration for SEOMetadataTemplate model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wagtail_seotoolkit", "0009_remove_is_verified_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="SEOMetadataTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="A descriptive name for this template (e.g., 'Blog Post Title', 'Product Description')",
                        max_length=100,
                    ),
                ),
                (
                    "template_type",
                    models.CharField(
                        choices=[
                            ("title", "SEO Title"),
                            ("description", "Meta Description"),
                        ],
                        help_text="Whether this template is for titles or descriptions",
                        max_length=20,
                    ),
                ),
                (
                    "template_content",
                    models.TextField(
                        help_text="Template content. Use placeholders like {title}, {site_name}, etc. Add [:N] to truncate.",
                        max_length=320,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        help_text="Leave blank for a template that works with all page types, or select a specific page type",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="seo_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "SEO Metadata Template",
                "verbose_name_plural": "SEO Metadata Templates",
                "ordering": ["-created_at"],
            },
        ),
    ]
