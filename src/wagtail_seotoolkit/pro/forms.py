# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Django forms for JSON-LD schema editing.

These forms enable editing StreamFields outside of Wagtail's standard
page edit interface.

Licensed under the WAYF Proprietary License.
"""

from django import forms
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page

from wagtail_seotoolkit.pro.models import (
    JSONLDSchemaTemplate,
    PageJSONLDOverride,
    SiteWideJSONLDSchema,
)


def get_page_content_types():
    """
    Get ContentTypes for page types that exist in the database.
    Same approach as SEO template settings.
    """
    return (
        ContentType.objects.filter(
            id__in=Page.objects.values_list("content_type_id", flat=True).distinct()
        )
        .exclude(app_label="wagtailcore")
        .order_by("app_label", "model")
    )


class JSONLDSchemaTemplateForm(forms.ModelForm):
    """Form for creating/editing JSON-LD schema templates."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter content_type to only show page models (same as SEO template settings)
        self.fields["content_type"].queryset = get_page_content_types()
        self.fields["content_type"].required = False
        self.fields["content_type"].empty_label = "All Page Types (Default)"

    class Meta:
        model = JSONLDSchemaTemplate
        fields = ["name", "content_type", "schemas", "is_active"]


class SiteWideJSONLDSchemaForm(forms.ModelForm):
    """Form for editing site-wide JSON-LD schemas."""

    class Meta:
        model = SiteWideJSONLDSchema
        fields = ["schemas", "is_active"]


class PageJSONLDOverrideForm(forms.ModelForm):
    """Form for editing page-specific JSON-LD overrides."""

    class Meta:
        model = PageJSONLDOverride
        fields = ["use_template", "schemas", "is_active"]
