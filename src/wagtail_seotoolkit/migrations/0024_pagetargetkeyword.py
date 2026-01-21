# Generated migration for PageTargetKeyword model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0094_alter_page_locale"),
        ("wagtail_seotoolkit", "0023_alter_draftseoauditissue_issue_type_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageTargetKeyword",
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
                    "keyword",
                    models.CharField(
                        help_text="Single target keyword",
                        max_length=255,
                    ),
                ),
                (
                    "position",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Order position (first keyword = primary)",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "page",
                    models.ForeignKey(
                        help_text="The page this keyword is associated with",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_keywords",
                        to="wagtailcore.page",
                    ),
                ),
            ],
            options={
                "verbose_name": "Page Target Keyword",
                "verbose_name_plural": "Page Target Keywords",
                "ordering": ["position", "id"],
                "unique_together": {("page", "keyword")},
            },
        ),
    ]
