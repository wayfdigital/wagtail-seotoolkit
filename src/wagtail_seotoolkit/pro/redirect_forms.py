# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Forms for redirect selection when deleting or unpublishing pages.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.admin.widgets import AdminPageChooser


class RedirectSelectionForm(forms.Form):
    """
    Dynamic form for selecting redirect targets for pages being deleted/unpublished.

    Creates a page chooser field for each page that needs a redirect.
    """

    def __init__(self, pages_data, *args, **kwargs):
        """
        Initialize the form with dynamic fields for each page.

        Args:
            pages_data: List of dicts with page information:
                - id: Page ID
                - title: Page title
                - url: Page URL
                - reference_count: Number of references to this page
                - group: 'main', 'children', or 'translations'
        """
        super().__init__(*args, **kwargs)
        self.pages_data = pages_data

        for page_data in pages_data:
            field_name = f"redirect_{page_data['id']}"
            self.fields[field_name] = forms.IntegerField(
                required=False,
                widget=AdminPageChooser(
                    target_models=["wagtailcore.page"],
                    can_choose_root=False,
                ),
                label=_('Redirect target for "%(title)s"')
                % {"title": page_data["title"]},
                help_text=_(
                    "Select a page to redirect %(url)s to. "
                    "Leave empty to skip creating a redirect for this page."
                )
                % {"url": page_data["url"]},
            )

    def clean(self):
        """
        Validate redirect selections:
        1. At least the main page must have a redirect selected
        2. Redirect targets cannot be pages that are also being deleted/unpublished
        """
        cleaned_data = super().clean()

        # Get all page IDs being deleted/unpublished
        page_ids_being_removed = {page_data["id"] for page_data in self.pages_data}

        # Find the main page
        main_page = next((p for p in self.pages_data if p["group"] == "main"), None)

        # Validate that at least the main page has a redirect selected
        if main_page:
            main_field_name = f"redirect_{main_page['id']}"
            main_redirect_target = cleaned_data.get(main_field_name)
            if not main_redirect_target:
                self.add_error(
                    main_field_name,
                    _(
                        "Please select a redirect target for the main page. "
                        "If you don't want to create any redirects, use the "
                        '"Skip" button instead.'
                    ),
                )

        # Validate that redirect targets are not pages being deleted/unpublished
        for page_data in self.pages_data:
            field_name = f"redirect_{page_data['id']}"
            redirect_target_id = cleaned_data.get(field_name)

            if redirect_target_id and redirect_target_id in page_ids_being_removed:
                self.add_error(
                    field_name,
                    _(
                        "Cannot redirect to a page that is also being "
                        "deleted/unpublished. Please choose a different page."
                    ),
                )

        return cleaned_data

    def get_redirect_mappings(self):
        """
        Get a dictionary mapping page IDs to their redirect target IDs.

        Returns:
            Dict mapping source page ID to target page ID (only for pages with targets selected)
        """
        if not self.is_valid():
            return {}

        mappings = {}
        for page_data in self.pages_data:
            field_name = f"redirect_{page_data['id']}"
            target_id = self.cleaned_data.get(field_name)
            if target_id:
                mappings[page_data["id"]] = target_id

        return mappings
