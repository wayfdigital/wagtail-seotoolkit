"""
Django app configuration for Wagtail SEO Toolkit
"""

from django.apps import AppConfig


class WagtailSEOToolkitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wagtail_seotoolkit'
    verbose_name = 'Wagtail SEO Toolkit'
    
    def ready(self):
        """Import hooks when the app is ready"""
        from . import wagtail_hooks  # noqa
