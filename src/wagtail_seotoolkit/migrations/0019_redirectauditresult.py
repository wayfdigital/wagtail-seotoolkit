# Generated migration for RedirectAuditResult model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_seotoolkit', '0018_simplify_site_wide_schemas'),
    ]

    operations = [
        migrations.CreateModel(
            name='RedirectAuditResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_redirects', models.IntegerField(default=0, help_text='Total number of redirects in the system')),
                ('chains_detected', models.IntegerField(default=0, help_text='Number of redirect chains longer than 1 hop')),
                ('circular_loops', models.IntegerField(default=0, help_text='Number of circular redirect loops detected')),
                ('redirects_to_404', models.IntegerField(default=0, help_text='Number of redirects pointing to 404/deleted pages')),
                ('redirects_to_unpublished', models.IntegerField(default=0, help_text='Number of redirects pointing to unpublished pages')),
                ('external_redirects', models.IntegerField(default=0, help_text='Number of redirects to external URLs')),
                ('chains_flattened', models.IntegerField(default=0, help_text='Number of redirect chains flattened during this audit')),
                ('audit_details', models.JSONField(blank=True, default=dict, help_text='Detailed information about problematic redirects (chains, loops, 404s)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('audit_run', models.OneToOneField(help_text='The SEO audit run this redirect audit belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='redirect_audit', to='wagtail_seotoolkit.seoauditrun')),
            ],
            options={
                'verbose_name': 'Redirect Audit Result',
                'verbose_name_plural': 'Redirect Audit Results',
                'ordering': ['-created_at'],
            },
        ),
    ]
