# Generated migration for BrokenLinkAuditResult model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_seotoolkit', '0019_redirectauditresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrokenLinkAuditResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_pages_scanned', models.IntegerField(default=0, help_text='Total number of pages scanned for broken links')),
                ('total_links_checked', models.IntegerField(default=0, help_text='Total number of links checked')),
                ('broken_internal_links', models.IntegerField(default=0, help_text='Number of internal links pointing to deleted pages')),
                ('links_to_unpublished', models.IntegerField(default=0, help_text='Number of internal links pointing to unpublished pages')),
                ('broken_external_links', models.IntegerField(default=0, help_text='Number of external links that return errors')),
                ('audit_details', models.JSONField(blank=True, default=dict, help_text='Detailed information about broken links found')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('audit_run', models.OneToOneField(help_text='The SEO audit run this broken link audit belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='broken_link_audit', to='wagtail_seotoolkit.seoauditrun')),
            ],
            options={
                'verbose_name': 'Broken Link Audit Result',
                'verbose_name_plural': 'Broken Link Audit Results',
                'ordering': ['-created_at'],
            },
        ),
    ]
