"""
Django app configuration for Wagtail SEO Toolkit
"""

from django.apps import AppConfig


class WagtailSEOToolkitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_seotoolkit"
    verbose_name = "Wagtail SEO Toolkit"

    def ready(self):
        """Import hooks when the app is ready"""
        from . import wagtail_hooks  # noqa

        # Monkey patch the get_side_panels method to add our custom side panel
        # Currently there's no hook to extend the side panels
        from wagtail.admin.views.pages.create import CreateView
        from wagtail.admin.views.pages.edit import EditView

        from wagtail_seotoolkit.core.ui.get_side_panels import get_side_panels

        EditView.get_side_panels_og = EditView.get_side_panels
        CreateView.get_side_panels_og = CreateView.get_side_panels

        EditView.get_side_panels = get_side_panels
        CreateView.get_side_panels = get_side_panels

        # Add information panel to the promote tab in the page editor
        from wagtail.admin.panels import HelpPanel
        from wagtail.models import Page

        Page.promote_panels.insert(
            1,
            HelpPanel(template="wagtail_seotoolkit/promote_panel_buttons.html"),
        )
