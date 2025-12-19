# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Views for redirect selection when deleting or unpublishing pages.
"""

import logging

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from wagtail.admin import messages
from wagtail.models import Page

from .redirect_forms import RedirectSelectionForm
from .utils.redirect_utils import (
    create_redirect,
    get_pages_for_redirect_prompt,
    replace_page_references,
)

logger = logging.getLogger(__name__)


class RedirectOnActionView(FormView):
    """
    View for selecting redirect targets before deleting or unpublishing pages.

    This view is triggered by the before_delete_page and before_unpublish_page hooks
    when a page being deleted/unpublished has references elsewhere on the site.
    """

    template_name = "wagtail_seotoolkit/confirm_redirect.html"
    form_class = RedirectSelectionForm

    def dispatch(self, request, *args, **kwargs):
        self.page_id = kwargs.get("page_id")
        self.action = kwargs.get("action", "delete")  # 'delete' or 'unpublish'
        self.page = get_object_or_404(Page, pk=self.page_id).specific

        # Get pages that need redirect prompts
        self.pages_data = get_pages_for_redirect_prompt(self.page)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["pages_data"] = self.pages_data
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = self.page
        context["action"] = self.action
        context["action_display"] = (
            _("delete") if self.action == "delete" else _("unpublish")
        )
        context["pages_data"] = self.pages_data

        # Group pages for display
        context["main_page"] = next(
            (p for p in self.pages_data if p["group"] == "main"), None
        )
        context["children_pages"] = [
            p for p in self.pages_data if p["group"] == "children"
        ]
        context["translation_pages"] = [
            p for p in self.pages_data if p["group"] == "translations"
        ]

        # URLs for form actions
        if self.action == "delete":
            context["proceed_url"] = reverse(
                "wagtailadmin_pages:delete", args=[self.page_id]
            )
        else:
            context["proceed_url"] = reverse(
                "wagtailadmin_pages:unpublish", args=[self.page_id]
            )

        context["cancel_url"] = reverse(
            "wagtailadmin_explore", args=[self.page.get_parent().id]
        )

        return context

    def form_valid(self, form):
        """
        Create redirects for selected pages and proceed with the action.

        For delete actions, also update all references to point to the new target
        pages, since internal links will break when the page is deleted.
        """
        redirect_mappings = form.get_redirect_mappings()
        redirects_created = 0
        references_updated = 0

        for source_page_id, target_page_id in redirect_mappings.items():
            source_page = Page.objects.get(pk=source_page_id)
            target_page = Page.objects.get(pk=target_page_id)

            # Get the URL of the source page before it's deleted/unpublished
            source_url = source_page.url
            if source_url:
                try:
                    redirect_obj, created = create_redirect(target_page, source_url)
                    if created:
                        redirects_created += 1
                        logger.info(
                            f"Created redirect from {source_url} to {target_page.url} "
                            f"before {self.action}"
                        )
                except Exception as e:
                    logger.error(f"Failed to create redirect: {e}")
                    messages.error(
                        self.request,
                        _('Failed to create redirect for "%(title)s": %(error)s')
                        % {
                            "title": source_page.title,
                            "error": str(e),
                        },
                    )

            # For delete actions, also update all references to the source page
            # to point to the target page instead
            if self.action == "delete":
                try:
                    updated = replace_page_references(source_page, target_page)
                    references_updated += updated
                    if updated > 0:
                        logger.info(
                            f"Updated {updated} reference(s) from page {source_page_id} "
                            f"to page {target_page_id}"
                        )
                except Exception as e:
                    logger.error(f"Failed to update references: {e}")
                    messages.warning(
                        self.request,
                        _(
                            'Some references to "%(title)s" could not be '
                            "automatically updated: %(error)s"
                        )
                        % {
                            "title": source_page.title,
                            "error": str(e),
                        },
                    )

        if redirects_created > 0:
            messages.success(
                self.request,
                _("Created %(count)d redirect(s).") % {"count": redirects_created},
            )

        if references_updated > 0:
            messages.success(
                self.request,
                _("Updated %(count)d page(s) with new references.")
                % {"count": references_updated},
            )

        # Set session flag to skip the hook on the actual delete/unpublish
        self.request.session[f"skip_redirect_prompt_{self.page_id}"] = True

        # Redirect to the actual delete/unpublish page
        if self.action == "delete":
            return redirect("wagtailadmin_pages:delete", self.page_id)
        else:
            return redirect("wagtailadmin_pages:unpublish", self.page_id)

    def post(self, request, *args, **kwargs):
        """
        Handle both form submission and skip action.
        """
        if "skip" in request.POST:
            # User chose to skip creating redirects
            self.request.session[f"skip_redirect_prompt_{self.page_id}"] = True

            if self.action == "delete":
                return redirect("wagtailadmin_pages:delete", self.page_id)
            else:
                return redirect("wagtailadmin_pages:unpublish", self.page_id)

        return super().post(request, *args, **kwargs)
