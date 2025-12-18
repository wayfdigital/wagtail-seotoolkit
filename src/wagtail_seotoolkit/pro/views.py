# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Pro views for bulk editor, subscriptions, and templates.

Licensed under the WAYF Proprietary License.
"""

import json

import django_filters
import requests
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.reports import ReportView
from wagtail.models import Page

from wagtail_seotoolkit.core.models import (
    SEOAuditIssueType,
)
from wagtail_seotoolkit.pro.models import (
    PluginEmailVerification,
    SEOMetadataTemplate,
)
from wagtail_seotoolkit.pro.utils.placeholder_utils import (
    get_placeholders_for_content_type,
    process_placeholders,
    validate_template_placeholders,
)

# License server API base URL
LICENSE_SERVER_API_URL = "https://wagtail-seotoolkit-license-server.vercel.app"


class GetEmailVerificationView(View):
    """
    API endpoint to get stored email verification data.
    Returns the stored email if exists, otherwise null.
    Verification status must be checked via external API.
    """

    def get(self, request):
        try:
            from wagtail_seotoolkit.pro.models import SubscriptionLicense

            verification = PluginEmailVerification.objects.first()
            subscription_license = SubscriptionLicense.objects.first()

            if verification:
                return JsonResponse(
                    {
                        "success": True,
                        "email": verification.email,
                        "instance_id": str(subscription_license.instance_id)
                        if subscription_license
                        else None,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": True,
                        "email": None,
                        "instance_id": str(subscription_license.instance_id)
                        if subscription_license
                        else None,
                    }
                )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to retrieve email: {str(e)}"},
                status=500,
            )


class SaveEmailVerificationView(View):
    """
    API endpoint to save or update email verification data.
    Only stores the email - verification status must be checked via external API.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Update or create verification record (only stores email, not verification status)
            verification, created = PluginEmailVerification.objects.get_or_create(
                email=email
            )

            # Also ensure SubscriptionLicense exists (with instance_id)
            # This allows subscription checks to work immediately after email verification
            from wagtail_seotoolkit.pro.models import SubscriptionLicense

            subscription_license, license_created = (
                SubscriptionLicense.objects.get_or_create()
            )

            # Automatically register this instance with the license server
            # This allows users to access pro features immediately after purchasing
            instance_id = str(subscription_license.instance_id)
            site_url = request.build_absolute_uri("/").rstrip("/")

            try:
                # Call register-instance API endpoint
                register_response = requests.post(
                    f"{LICENSE_SERVER_API_URL}/api/register-instance",
                    json={
                        "email": email,
                        "instanceId": instance_id,
                        "siteUrl": site_url,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )

                # Clear subscription cache so UI updates immediately
                # (Cache is disabled in DEBUG mode, so this is a no-op there)
                if register_response.status_code == 200:
                    from django.conf import settings
                    from django.core.cache import cache

                    if not getattr(settings, "DEBUG", False):
                        cache_key = f"subscription:{email}:{instance_id}"
                        cache.delete(cache_key)
                else:
                    # Log registration attempt but don't fail if it doesn't work
                    print(
                        f"Warning: Failed to auto-register instance: {register_response.text}"
                    )
            except Exception as reg_error:
                # Don't fail email verification if registration fails
                print(f"Warning: Failed to auto-register instance: {str(reg_error)}")

            return JsonResponse(
                {
                    "success": True,
                    "message": "Email saved successfully",
                    "email": verification.email,
                    "instance_id": instance_id,
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to save email: {str(e)}"},
                status=500,
            )


class DeleteEmailVerificationView(View):
    """
    API endpoint to delete stored email verification data.
    Used when user wants to change their email.
    """

    def post(self, request):
        try:
            # Delete all email verification records
            deleted_count = PluginEmailVerification.objects.all().delete()[0]

            return JsonResponse(
                {
                    "success": True,
                    "message": "Email verification data deleted successfully",
                    "deleted_count": deleted_count,
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to delete email: {str(e)}"},
                status=500,
            )


class ProxyGetDashboardMessageView(View):
    """
    Proxy endpoint to get dashboard message from external API.
    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        try:
            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/get-dashboard-message",
                timeout=5,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": None,
                    "hasMessage": False,
                    "error": f"Failed to fetch message: {str(e)}",
                },
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": None,
                    "hasMessage": False,
                    "error": str(e),
                },
                status=500,
            )


class ProxySendVerificationView(View):
    """
    Proxy endpoint to send verification email via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/send-verification",
                json={"email": email},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to send verification: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error: {str(e)}"}, status=500
            )


class ProxyCheckVerifiedView(View):
    """
    Proxy endpoint to check verification status via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        email = request.GET.get("email")

        if not email:
            return JsonResponse(
                {"verified": False, "pending": False, "error": "Email is required"},
                status=400,
            )

        try:
            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/check-verified",
                params={"email": email},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "verified": False,
                    "pending": False,
                    "error": f"Failed to check verification: {str(e)}",
                },
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {"verified": False, "pending": False, "error": f"Error: {str(e)}"},
                status=500,
            )


class ProxyResendVerificationView(View):
    """
    Proxy endpoint to resend verification email via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"}, status=400
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/resend-verification",
                json={"email": email},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Failed to resend verification: {str(e)}",
                },
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error: {str(e)}"}, status=500
            )


class ProxyGetPlansView(View):
    """
    Proxy endpoint to get available subscription plans via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        try:
            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/get-plans",
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to get plans: {str(e)}"},
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyCheckSubscriptionView(View):
    """
    Proxy endpoint to check subscription status via external API.

    Caching behavior:
    - Production: Only Pro responses are cached for 24 hours
    - Non-Pro responses are never cached (immediate feedback on upgrades)
    - DEBUG mode: All caching is disabled for development

    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        from django.conf import settings
        from django.core.cache import cache

        email = request.GET.get("email")
        instance_id = request.GET.get("instanceId")

        if not email or not instance_id:
            return JsonResponse(
                {"pro": False, "error": "Email and instanceId are required"},
                status=400,
            )

        try:
            # Skip caching in DEBUG mode for development
            use_cache = not getattr(settings, "DEBUG", False)

            # Check cache first (24 hour TTL) - only if not in DEBUG mode
            # Note: We only cache Pro responses, so non-pro users get immediate feedback on upgrade
            cache_key = f"subscription:{email}:{instance_id}"
            if use_cache:
                cached_data = cache.get(cache_key)
                if cached_data:
                    return JsonResponse(cached_data)

            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/check-subscription",
                params={"email": email, "instanceId": instance_id},
                timeout=10,
            )

            data = response.json()

            # Cache ONLY Pro responses for 24 hours (86400 seconds) in production
            # Non-pro responses are never cached so users see upgrades immediately
            if use_cache and response.status_code == 200 and data.get("pro") is True:
                cache.set(cache_key, data, 86400)

            return JsonResponse(data, status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"pro": False, "error": f"Failed to check subscription: {str(e)}"},
                status=500,
            )
        except Exception as e:
            return JsonResponse({"pro": False, "error": f"Error: {str(e)}"}, status=500)


class ProxyCreateCheckoutView(View):
    """
    Proxy endpoint to create Stripe checkout session via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            price_id = data.get("priceId")
            return_url = data.get("returnUrl")

            if not email or not price_id or not return_url:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Email, priceId, and returnUrl are required",
                    },
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/create-checkout-session",
                json={"email": email, "priceId": price_id, "returnUrl": return_url},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to create checkout: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyRegisterInstanceView(View):
    """
    Proxy endpoint to register instance to subscription via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            instance_id = data.get("instanceId")
            site_url = data.get("siteUrl", "")

            if not email or not instance_id:
                return JsonResponse(
                    {"success": False, "error": "Email and instanceId are required"},
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/register-instance",
                json={"email": email, "instanceId": instance_id, "siteUrl": site_url},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Clear cache on successful registration
            # (Cache is disabled in DEBUG mode, so this is a no-op there)
            if response.status_code == 200:
                from django.conf import settings
                from django.core.cache import cache

                if not getattr(settings, "DEBUG", False):
                    cache_key = f"subscription:{email}:{instance_id}"
                    cache.delete(cache_key)

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to register instance: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyListInstancesView(View):
    """
    Proxy endpoint to list all instances for an email via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        email = request.GET.get("email")

        if not email:
            return JsonResponse(
                {"success": False, "error": "Email is required"}, status=400
            )

        try:
            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/list-instances",
                params={"email": email},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to list instances: {str(e)}"},
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyRemoveInstanceView(View):
    """
    Proxy endpoint to remove instance from subscription via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            instance_id = data.get("instanceId")

            if not email or not instance_id:
                return JsonResponse(
                    {"success": False, "error": "Email and instanceId are required"},
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/remove-instance",
                json={"email": email, "instanceId": instance_id},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Clear cache on successful removal
            # (Cache is disabled in DEBUG mode, so this is a no-op there)
            if response.status_code == 200:
                from django.conf import settings
                from django.core.cache import cache

                if not getattr(settings, "DEBUG", False):
                    cache_key = f"subscription:{email}:{instance_id}"
                    cache.delete(cache_key)

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to remove instance: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyCreatePortalView(View):
    """
    Proxy endpoint to create Stripe customer portal session via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            instance_id = data.get("instanceId")
            return_url = data.get("returnUrl")

            if not email or not instance_id or not return_url:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Email, instanceId, and returnUrl are required",
                    },
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/create-portal-session",
                json={
                    "email": email,
                    "instanceId": instance_id,
                    "returnUrl": return_url,
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Failed to create portal: {str(e)}"},
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyGetActiveInstancesView(View):
    """
    Proxy endpoint to get active instances via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def get(self, request):
        email = request.GET.get("email")

        if not email:
            return JsonResponse(
                {"success": False, "error": "Email is required"}, status=400
            )

        try:
            # Make request to external API
            response = requests.get(
                f"{LICENSE_SERVER_API_URL}/api/get-active-instances",
                params={"email": email},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to get active instances: {str(e)}",
                },
                status=500,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxySetActiveInstancesView(View):
    """
    Proxy endpoint to set active instances via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            instance_ids = data.get("instanceIds")

            if not email or instance_ids is None:
                return JsonResponse(
                    {"success": False, "error": "Email and instanceIds are required"},
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/set-active-instances",
                json={"email": email, "instanceIds": instance_ids},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Note: Cache clearing for active instances is handled by TTL
            # Individual instance checks will refresh on next request

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to set active instances: {str(e)}",
                },
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class ProxyClearActiveInstancesView(View):
    """
    Proxy endpoint to clear active instances via external API.
    Avoids CORS issues by making server-to-server request.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse(
                    {"success": False, "error": "Email is required"},
                    status=400,
                )

            # Make request to external API
            response = requests.post(
                f"{LICENSE_SERVER_API_URL}/api/clear-active-instances",
                json={"email": email},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            # Return the external API response
            return JsonResponse(response.json(), status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to clear active instances: {str(e)}",
                },
                status=500,
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error: {str(e)}"}, status=500
            )


class BulkEditFilterSet(WagtailFilterSet):
    """FilterSet for Bulk Editor"""

    issue_type = django_filters.MultipleChoiceFilter(
        label=_("Issue Type"),
        field_name="seo_issues__issue_type",
        method="filter_issue_type",
        choices=list(
            filter(
                lambda x: SEOAuditIssueType.is_bulk_edit_issue(x[0]),
                SEOAuditIssueType.choices,
            )
        ),
        widget=forms.CheckboxSelectMultiple,
    )

    content_type = django_filters.ModelMultipleChoiceFilter(
        label=_("Page Type"),
        queryset=ContentType.objects.filter(
            id__in=Page.objects.values_list("content_type_id", flat=True).distinct()
        )
        .exclude(app_label="wagtailcore")
        .order_by("app_label", "model"),
        field_name="content_type",
        widget=forms.CheckboxSelectMultiple,
    )

    def filter_issue_type(self, queryset, name, value):
        """Filter pages by issue types from the latest audit run only"""
        if not value:
            return queryset

        # Get the latest completed audit run
        from wagtail_seotoolkit.core.models import SEOAuditRun

        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )

        if not latest_audit:
            # No completed audit yet, return empty queryset
            return queryset.none()

        # Filter pages that have the selected issue types in the latest audit run
        return queryset.filter(
            seo_issues__audit_run=latest_audit, seo_issues__issue_type__in=value
        ).distinct()

    class Meta:
        model = Page
        fields = ["locale"]


class BulkEditView(ReportView):
    """
    Bulk editor view showing all pages for SEO metadata editing
    """

    index_url_name = "bulk_edit"
    index_results_url_name = "bulk_edit_results"
    page_title = _("Bulk SEO Editor")
    header_icon = "edit"
    template_name = "wagtail_seotoolkit/bulk_edit_base.html"
    results_template_name = "wagtail_seotoolkit/bulk_edit_results.html"

    model = Page
    filterset_class = BulkEditFilterSet

    list_export = [
        "title",
        "seo_title",
        "search_description",
        "last_published_at",
    ]

    def get_queryset(self):
        # Get all pages, excluding the root page and alias pages
        return (
            Page.objects.exclude(depth=1)
            .exclude(alias_of_id__isnull=False)  # Exclude alias pages
            .select_related("locale", "content_type")
            .prefetch_related("seo_issues")
            .order_by("-last_published_at")
        )

    def get_breadcrumbs_items(self):
        """Add SEO Dashboard to breadcrumbs"""
        from django.urls import reverse

        return [
            {
                "url": reverse("seo_dashboard"),
                "label": _("SEO Dashboard"),
            },
            {
                "url": None,
                "label": _("Bulk SEO Editor"),
            },
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Alias object_list for template consistency
        context["pages"] = context.get("object_list", [])

        # Check subscription status for bulk editor access
        from wagtail_seotoolkit.pro.models import (
            PluginEmailVerification,
            SubscriptionLicense,
        )

        # Get email from PluginEmailVerification (single source of truth)
        verification = PluginEmailVerification.objects.first()
        email = verification.email if verification else None

        # Get or create instance ID from SubscriptionLicense
        # Ensures instance_id exists even if email was verified before subscription system was added
        if email and not SubscriptionLicense.objects.exists():
            license = SubscriptionLicense.objects.create()

            # Auto-register this instance with the license server
            try:
                instance_id = str(license.instance_id)
                site_url = self.request.build_absolute_uri("/").rstrip("/")

                requests.post(
                    f"{LICENSE_SERVER_API_URL}/api/register-instance",
                    json={
                        "email": email,
                        "instanceId": instance_id,
                        "siteUrl": site_url,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
            except Exception as e:
                # Don't fail page load if registration fails
                print(
                    f"Warning: Failed to auto-register instance in BulkEditView: {str(e)}"
                )

        license = SubscriptionLicense.objects.first()
        instance_id = str(license.instance_id) if license else None

        context["subscription_email"] = email
        context["subscription_instance_id"] = instance_id

        # Check for unprocessed placeholder issues in latest audit
        from django.conf import settings

        from wagtail_seotoolkit.core.models import SEOAuditIssueType, SEOAuditRun
        
        # Only check if middleware processing is disabled
        process_placeholders_enabled = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS", True
        )
        
        if not process_placeholders_enabled:
            latest_audit = SEOAuditRun.objects.filter(status="completed").order_by("-created_at").first()
            if latest_audit:
                placeholder_issues_count = latest_audit.issues.filter(
                    issue_type=SEOAuditIssueType.PLACEHOLDER_UNPROCESSED
                ).count()
                context["has_placeholder_issues"] = placeholder_issues_count > 0
                context["placeholder_issues_count"] = placeholder_issues_count
            else:
                context["has_placeholder_issues"] = False
                context["placeholder_issues_count"] = 0
        else:
            context["has_placeholder_issues"] = False
            context["placeholder_issues_count"] = 0

        return context


@require_POST
def preview_metadata(request):
    """
    API endpoint to preview how placeholders will be processed for selected pages.
    Returns processed values for each page to show in preview table.
    """
    try:
        page_ids = request.POST.getlist("page_ids")
        template = request.POST.get("template", "").strip()
        action = request.POST.get("action", "edit_title")

        if not page_ids or not template:
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        previews = []
        for page in pages:
            # Get the latest revision to show current values
            latest_revision = page.get_latest_revision()
            if latest_revision:
                page_instance = latest_revision.as_object()
            else:
                page_instance = page.specific

            # Get current SEO values from page fields
            if action == "edit_title":
                current_value_raw = page_instance.seo_title or ""
            else:  # edit_description
                current_value_raw = page_instance.search_description or ""

            # Process placeholders in current value
            current_value = (
                process_placeholders(current_value_raw, page_instance, request)
                if current_value_raw
                else ""
            )

            # Process template for this page
            processed_value = process_placeholders(template, page_instance, request)

            previews.append(
                {
                    "page_id": page.id,
                    "page_title": page.title,
                    "page_type": page.page_type_display_name,
                    "current_value": current_value,
                    "new_value": processed_value,
                }
            )

        return JsonResponse({"success": True, "previews": previews})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def validate_metadata_bulk(request):
    """
    API endpoint to validate SEO metadata for multiple pages.

    Validates either titles or meta descriptions based on action parameter,
    and returns validation results for each page including issues and severity.

    Expected POST data:
        - page_ids: List of page IDs
        - template: Template string with placeholders
        - action: Either "edit_title" or "edit_description"

    Returns:
        JSON with validation results for each page
    """
    try:
        from wagtail_seotoolkit.core.utils.seo_validators import (
            validate_meta_description,
            validate_title,
        )

        page_ids = request.POST.getlist("page_ids")
        template = request.POST.get("template", "").strip()
        action = request.POST.get("action", "edit_title")

        if not page_ids:
            return JsonResponse(
                {"success": False, "error": "Missing page_ids parameter"}, status=400
            )

        pages = Page.objects.filter(id__in=page_ids).select_related("content_type")

        validations = []
        for page in pages:
            # Get the latest revision
            latest_revision = page.get_latest_revision()
            if latest_revision:
                page_instance = latest_revision.as_object()
            else:
                page_instance = page.specific

            # Process template to get the actual value
            if template:
                processed_value = process_placeholders(template, page_instance, request)
            else:
                # If no template, use current value
                if action == "edit_title":
                    processed_value = page_instance.seo_title or ""
                else:  # edit_description
                    processed_value = page_instance.search_description or ""

            # Validate based on action type
            if action == "edit_title":
                validation_result = validate_title(processed_value)
            else:  # edit_description
                validation_result = validate_meta_description(processed_value)

            validations.append(
                {
                    "page_id": page.id,
                    "page_title": page.title,
                    "value": processed_value,
                    **validation_result,
                }
            )

        return JsonResponse({"success": True, "validations": validations})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def bulk_apply_metadata(request):
    """
    API endpoint to apply bulk metadata changes.
    
    Behavior depends on WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS setting:
    - If True (default): Saves templates with placeholders; middleware processes them at runtime
    - If False: Processes placeholders immediately and saves the final values
    
    Automatically publishes revisions for live pages without unpublished changes.
    """
    from django.conf import settings
    
    try:
        page_ids = request.POST.getlist("page_ids")
        action = request.POST.get("action")
        content_template = request.POST.get("content", "").strip()

        if not page_ids or not action or not content_template:
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        # Check if middleware processing is enabled
        # If True: save templates with placeholders (middleware will process them)
        # If False: process placeholders now and save final values
        process_placeholders_enabled = getattr(
            settings, "WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS", True
        )

        pages = Page.objects.filter(id__in=page_ids)

        # Track which pages to publish (must check BEFORE creating revisions)
        pages_to_publish = []
        pages_to_leave_draft = []
        skipped_pages = []  # Track pages that couldn't be processed

        for page in pages:
            # Skip alias pages - they cannot have revisions
            if page.alias_of_id:
                skipped_pages.append({
                    "id": page.id,
                    "title": page.title,
                    "reason": "Alias pages cannot be edited through bulk metadata editor. Please edit the original page instead."
                })
                continue
            
            # Check if page should be auto-published
            # Must check has_unpublished_changes BEFORE creating revision
            should_publish = page.live and not page.has_unpublished_changes

            # Determine which version to use as base:
            # - If page has unpublished changes: use latest revision to preserve those changes
            # - If page has no unpublished changes: use live page (page.specific) to ensure all data is current
            if page.has_unpublished_changes:
                page_instance = page.get_latest_revision_as_object()
                
                # IMPORTANT: Check if revision is missing required fields and copy them from live page
                # This happens when revisions are older than new required fields
                if page.live:
                    live_page = page.specific
                    for field in page_instance._meta.get_fields():
                        # Skip relation fields
                        if field.is_relation and not field.concrete:
                            continue
                        # Check if field is required and empty in revision
                        if hasattr(field, 'blank') and hasattr(field, 'null'):
                            if not field.blank and not field.null and hasattr(page_instance, field.name):
                                field_value = getattr(page_instance, field.name, None)
                                if field_value is None or (isinstance(field_value, str) and field_value == ""):
                                    # Try to get value from live page
                                    live_value = getattr(live_page, field.name, None)
                                    if live_value:
                                        setattr(page_instance, field.name, live_value)
                else:
                    # Page is not live, check for empty required fields
                    has_empty_required = False
                    empty_fields = []
                    for field in page_instance._meta.get_fields():
                        # Skip relation fields
                        if field.is_relation and not field.concrete:
                            continue
                        # Check if field is required and empty
                        if hasattr(field, 'blank') and hasattr(field, 'null'):
                            if not field.blank and not field.null and hasattr(page_instance, field.name):
                                field_value = getattr(page_instance, field.name, None)
                                if field_value is None or (isinstance(field_value, str) and field_value == ""):
                                    has_empty_required = True
                                    empty_fields.append(field.name)
                    
                    if has_empty_required:
                        error_msg = f"Page has empty required fields ({', '.join(empty_fields)}) and is not live. Please complete the page before applying SEO metadata."
                        skipped_pages.append({
                            "id": page.id,
                            "title": page.title,
                            "reason": error_msg
                        })
                        continue  # Skip this page
            else:
                # No unpublished changes - use live page to ensure all fields are current
                page_instance = page.specific

            # Determine the value to save based on setting
            if process_placeholders_enabled:
                # Save template with placeholders (middleware will process at runtime)
                value_to_save = content_template
            else:
                # Process placeholders now and save final value
                value_to_save = process_placeholders(content_template, page_instance, request)

            # Update the appropriate field
            if action == "edit_title":
                page_instance.seo_title = value_to_save[:255]  # Respect max_length
            elif action == "edit_description":
                page_instance.search_description = value_to_save[:320]  # Respect max_length

            # Save as a new revision with proper log entry
            new_revision = page_instance.save_revision(
                user=request.user if request.user.is_authenticated else None,
                log_action=True,  # Create log entry for revision history
                changed=True,  # Mark that content has changed
            )

            # Publish if appropriate
            if should_publish:
                # Publish the revision with proper log action
                new_revision.publish(
                    user=request.user if request.user.is_authenticated else None,
                    log_action=True,  # Create log entry for publish action
                )
                pages_to_publish.append(
                    {
                        "id": page.id,
                        "title": page.title,
                    }
                )
            else:
                pages_to_leave_draft.append(
                    {
                        "id": page.id,
                        "title": page.title,
                    }
                )

        total_processed = len(pages_to_publish) + len(pages_to_leave_draft)

        # Build message
        message_parts = []
        if total_processed > 0:
            message_parts.append(f"Successfully updated {total_processed} page{'s' if total_processed != 1 else ''}")
            details = []
            if len(pages_to_publish) > 0:
                details.append(f"{len(pages_to_publish)} published")
            if len(pages_to_leave_draft) > 0:
                details.append(f"{len(pages_to_leave_draft)} left as draft")
            if details:
                message_parts.append(f"({', '.join(details)})")
        
        if len(skipped_pages) > 0:
            if message_parts:
                message_parts.append(". ")
            message_parts.append(f"{len(skipped_pages)} page{'s' if len(skipped_pages) != 1 else ''} skipped due to errors")

        return JsonResponse(
            {
                "success": True,
                "updated": total_processed,
                "published": len(pages_to_publish),
                "draft": len(pages_to_leave_draft),
                "skipped": len(skipped_pages),
                "published_pages": pages_to_publish,
                "draft_pages": pages_to_leave_draft,
                "skipped_pages": skipped_pages,
                "message": ''.join(message_parts) if message_parts else "No pages processed",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateListView(TemplateView):
    """
    View for listing all SEO metadata templates
    """

    template_name = "wagtail_seotoolkit/template_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        templates = SEOMetadataTemplate.objects.all().select_related(
            "created_by", "content_type"
        )

        context.update(
            {
                "templates": templates,
                "page_title": _("SEO Metadata Templates"),
            }
        )

        return context


class TemplateCreateView(TemplateView):
    """
    View for creating a new SEO metadata template
    """

    template_name = "wagtail_seotoolkit/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available content types (page types)
        page_content_types = (
            ContentType.objects.filter(
                id__in=Page.objects.values_list("content_type_id", flat=True).distinct()
            )
            .exclude(app_label="wagtailcore")
            .order_by("app_label", "model")
        )

        # Get initial placeholders (for "All Page Types")
        initial_placeholders = get_placeholders_for_content_type(None)

        context.update(
            {
                "page_title": _("Create SEO Template"),
                "is_create": True,
                "template_types": SEOMetadataTemplate.TEMPLATE_TYPE_CHOICES,
                "page_content_types": page_content_types,
                "placeholders": initial_placeholders,
            }
        )

        return context

    def post(self, request):
        """Handle template creation"""
        try:
            name = request.POST.get("name", "").strip()
            template_type = request.POST.get("template_type", "title")
            template_content = request.POST.get("template_content", "").strip()
            content_type_id = request.POST.get("content_type", "").strip()

            if not name:
                return JsonResponse(
                    {"success": False, "error": "Template name is required"}, status=400
                )

            if not template_content:
                return JsonResponse(
                    {"success": False, "error": "Template content is required"},
                    status=400,
                )

            # Get content type if specified
            content_type = None
            content_type_id_int = None
            if content_type_id:
                try:
                    content_type = ContentType.objects.get(id=content_type_id)
                    content_type_id_int = int(content_type_id)
                except ContentType.DoesNotExist:
                    pass

            # Validate placeholders
            is_valid, invalid_placeholders = validate_template_placeholders(
                template_content, content_type_id_int
            )

            if not is_valid:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Invalid placeholders detected: {', '.join(invalid_placeholders)}. "
                        f"These fields are not available for the selected page type.",
                    },
                    status=400,
                )

            template = SEOMetadataTemplate.objects.create(
                name=name,
                template_type=template_type,
                template_content=template_content,
                content_type=content_type,
                created_by=request.user if request.user.is_authenticated else None,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Template created successfully",
                    "template_id": template.id,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateEditView(TemplateView):
    """
    View for editing an existing SEO metadata template
    """

    template_name = "wagtail_seotoolkit/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        template_id = kwargs.get("template_id")
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)

            # Get available content types (page types)
            page_content_types = (
                ContentType.objects.filter(
                    id__in=Page.objects.values_list(
                        "content_type_id", flat=True
                    ).distinct()
                )
                .exclude(app_label="wagtailcore")
                .order_by("app_label", "model")
            )

            # Get placeholders for current content type
            placeholders = get_placeholders_for_content_type(
                template.content_type_id if template.content_type else None
            )

            context.update(
                {
                    "page_title": _("Edit SEO Template"),
                    "is_create": False,
                    "template": template,
                    "template_types": SEOMetadataTemplate.TEMPLATE_TYPE_CHOICES,
                    "page_content_types": page_content_types,
                    "placeholders": placeholders,
                }
            )
        except SEOMetadataTemplate.DoesNotExist:
            context.update({"error": "Template not found"})

        return context

    def post(self, request, template_id):
        """Handle template update"""
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)

            name = request.POST.get("name", "").strip()
            template_type = request.POST.get("template_type", "title")
            template_content = request.POST.get("template_content", "").strip()
            content_type_id = request.POST.get("content_type", "").strip()

            if not name:
                return JsonResponse(
                    {"success": False, "error": "Template name is required"}, status=400
                )

            if not template_content:
                return JsonResponse(
                    {"success": False, "error": "Template content is required"},
                    status=400,
                )

            # Get content type if specified
            content_type = None
            content_type_id_int = None
            if content_type_id:
                try:
                    content_type = ContentType.objects.get(id=content_type_id)
                    content_type_id_int = int(content_type_id)
                except ContentType.DoesNotExist:
                    pass

            # Validate placeholders
            is_valid, invalid_placeholders = validate_template_placeholders(
                template_content, content_type_id_int
            )

            if not is_valid:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Invalid placeholders detected: {', '.join(invalid_placeholders)}. "
                        f"These fields are not available for the selected page type.",
                    },
                    status=400,
                )

            template.name = name
            template.template_type = template_type
            template.template_content = template_content
            template.content_type = content_type
            template.save()

            return JsonResponse(
                {"success": True, "message": "Template updated successfully"}
            )

        except SEOMetadataTemplate.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Template not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class TemplateDeleteView(View):
    """
    View for deleting an SEO metadata template
    """

    def post(self, request, template_id):
        """Handle template deletion"""
        try:
            template = SEOMetadataTemplate.objects.get(id=template_id)
            template_name = template.name
            template.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Template "{template_name}" deleted successfully',
                }
            )

        except SEOMetadataTemplate.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Template not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


def get_placeholders_api(request):
    """
    API endpoint to get available placeholders for a content type.
    Returns JSON list of placeholder objects.
    """
    content_type_id = request.GET.get("content_type_id")

    try:
        # Convert to int if provided
        if content_type_id:
            content_type_id = int(content_type_id)
        else:
            content_type_id = None

        placeholders = get_placeholders_for_content_type(content_type_id)

        return JsonResponse({"success": True, "placeholders": placeholders})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def save_as_template(request):
    """
    API endpoint to save current bulk edit content as a new template
    """
    try:
        name = request.POST.get("name", "").strip()
        template_type = request.POST.get("template_type", "title")
        template_content = request.POST.get("template_content", "").strip()
        content_type_id = request.POST.get("content_type_id", "").strip()

        if not name:
            return JsonResponse(
                {"success": False, "error": "Template name is required"}, status=400
            )

        if not template_content:
            return JsonResponse(
                {"success": False, "error": "Template content is required"}, status=400
            )

        # Get content type if specified
        content_type = None
        if content_type_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
            except ContentType.DoesNotExist:
                pass

        # Check if template with same name exists
        existing = SEOMetadataTemplate.objects.filter(
            name=name, template_type=template_type
        ).first()

        if existing:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"A {template_type} template with name '{name}' already exists",
                },
                status=400,
            )

        template = SEOMetadataTemplate.objects.create(
            name=name,
            template_type=template_type,
            template_content=template_content,
            content_type=content_type,
            created_by=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Template '{name}' saved successfully",
                "template_id": template.id,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class BulkEditActionView(TemplateView):
    """
    View for bulk editing SEO titles or descriptions for selected pages
    """

    template_name = "wagtail_seotoolkit/bulk_edit_action.html"

    def get_available_placeholders(self, pages):
        """
        Get available field placeholders based on selected pages.
        Returns a list of dicts with field info.
        """
        # Get content types of selected pages
        content_types = set(page.content_type_id for page in pages) if pages else set()

        # If all pages are the same type, get placeholders for that type
        if len(content_types) == 1:
            content_type_id = list(content_types)[0]
            return get_placeholders_for_content_type(content_type_id)
        else:
            # Mixed or no pages - return universal placeholders
            return get_placeholders_for_content_type(None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get selected page IDs from URL parameters
        page_ids = self.request.GET.getlist("page_ids")
        action = self.request.GET.get("action", "edit_title")

        # Get the selected pages (excluding alias pages)
        pages = Page.objects.filter(id__in=page_ids).exclude(alias_of_id__isnull=False).select_related("content_type")

        # Process current values with placeholders
        pages_with_processed = []
        for page in pages:
            page_instance = page.specific

            # Get current value and process placeholders
            if action == "edit_title":
                current_raw = page_instance.seo_title or ""
            else:  # edit_description
                current_raw = page_instance.search_description or ""

            # Process placeholders in current value
            current_processed = (
                process_placeholders(current_raw, page_instance, self.request)
                if current_raw
                else ""
            )

            # Add processed value to page object
            page.current_processed = current_processed
            pages_with_processed.append(page)

        # Get available placeholders
        placeholders = self.get_available_placeholders(pages)

        # Determine template type based on action
        template_type = "title" if action == "edit_title" else "description"

        # Get content types of selected pages
        selected_content_types = set(page.content_type_id for page in pages)

        # Get templates: those with no content_type (all pages) or matching content_type
        # Only show templates if all selected pages are of the same type
        templates = (
            SEOMetadataTemplate.objects.filter(template_type=template_type)
            .filter(
                models.Q(content_type__isnull=True)
                | models.Q(content_type_id__in=selected_content_types)
            )
            .select_related("content_type")
        )

        # If multiple content types selected, only show "all pages" templates
        if len(selected_content_types) > 1:
            templates = templates.filter(content_type__isnull=True)

        # Get the content_type_id for save template feature
        content_type_id = None
        if len(selected_content_types) == 1:
            content_type_id = list(selected_content_types)[0]

        context.update(
            {
                "pages": pages_with_processed,
                "page_ids": page_ids,
                "action": action,
                "is_title": action == "edit_title",
                "is_description": action == "edit_description",
                "placeholders": placeholders,
                "templates": templates,
                "content_type_id": content_type_id,
                "template_type": template_type,
            }
        )

        return context


class SubscriptionSettingsView(TemplateView):
    """
    View for managing subscription and instance registration.
    Displays subscription status, instance management, and purchase options.
    """

    template_name = "wagtail_seotoolkit/subscription_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail_seotoolkit.pro.models import (
            PluginEmailVerification,
            SubscriptionLicense,
        )

        # Get email from PluginEmailVerification (single source of truth)
        verification = PluginEmailVerification.objects.first()
        email = verification.email if verification else None

        # Get or create instance ID from SubscriptionLicense
        # Ensures instance_id exists even if email was verified before subscription system was added
        if email and not SubscriptionLicense.objects.exists():
            license = SubscriptionLicense.objects.create()

            # Auto-register this instance with the license server
            try:
                instance_id = str(license.instance_id)
                site_url = self.request.build_absolute_uri("/").rstrip("/")

                requests.post(
                    f"{LICENSE_SERVER_API_URL}/api/register-instance",
                    json={
                        "email": email,
                        "instanceId": instance_id,
                        "siteUrl": site_url,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
            except Exception as e:
                # Don't fail page load if registration fails
                print(
                    f"Warning: Failed to auto-register instance in SubscriptionSettingsView: {str(e)}"
                )

        license = SubscriptionLicense.objects.first()

        context.update(
            {
                "license": license,
                "email": email,
                "instance_id": str(license.instance_id) if license else None,
            }
        )

        return context


# =============================================================================
# Redirect Dashboard View
# =============================================================================


class RedirectDashboardView(TemplateView):
    """
    Dashboard view for redirect management and health metrics.

    Displays:
    - Total redirect count
    - Redirect chains longer than 1 hop
    - Circular redirect loops
    - Redirects pointing to 404/deleted pages
    - Redirects to unpublished pages
    - Actions taken (chains flattened)
    """

    template_name = "wagtail_seotoolkit/redirect_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail.contrib.redirects.models import Redirect

        from wagtail_seotoolkit.core.models import SEOAuditRun
        from wagtail_seotoolkit.pro.models import RedirectAuditResult

        # Get latest redirect audit result
        latest_audit = (
            SEOAuditRun.objects.filter(status="completed")
            .order_by("-created_at")
            .first()
        )

        latest_redirect_audit = None
        if latest_audit:
            try:
                latest_redirect_audit = RedirectAuditResult.objects.get(
                    audit_run=latest_audit
                )
            except RedirectAuditResult.DoesNotExist:
                pass

        # Get current redirect counts (live data)
        total_redirects = Redirect.objects.count()

        if latest_redirect_audit:
            context.update(
                {
                    "has_audit_data": True,
                    "latest_audit": latest_audit,
                    "redirect_audit": latest_redirect_audit,
                    "total_redirects": latest_redirect_audit.total_redirects,
                    "chains_detected": latest_redirect_audit.chains_detected,
                    "circular_loops": latest_redirect_audit.circular_loops,
                    "redirects_to_404": latest_redirect_audit.redirects_to_404,
                    "redirects_to_unpublished": latest_redirect_audit.redirects_to_unpublished,
                    "external_redirects": latest_redirect_audit.external_redirects,
                    "chains_flattened": latest_redirect_audit.chains_flattened,
                    "health_score": latest_redirect_audit.health_score,
                    "has_issues": latest_redirect_audit.has_issues,
                    # Detailed audit data
                    "chain_details": latest_redirect_audit.audit_details.get(
                        "chains", []
                    )[:10],
                    "loop_details": latest_redirect_audit.audit_details.get(
                        "loops", []
                    )[:10],
                    "redirect_404_details": latest_redirect_audit.audit_details.get(
                        "redirects_to_404", []
                    )[:10],
                    "redirect_unpublished_details": latest_redirect_audit.audit_details.get(
                        "redirects_to_unpublished", []
                    )[:10],
                    "statistics": latest_redirect_audit.audit_details.get(
                        "statistics", {}
                    ),
                }
            )
        else:
            # No audit data - show current count but no health metrics
            context.update(
                {
                    "has_audit_data": False,
                    "latest_audit": None,
                    "redirect_audit": None,
                    "total_redirects": total_redirects,
                    "chains_detected": 0,
                    "circular_loops": 0,
                    "redirects_to_404": 0,
                    "redirects_to_unpublished": 0,
                    "external_redirects": 0,
                    "chains_flattened": 0,
                    "health_score": None,
                    "has_issues": False,
                    "chain_details": [],
                    "loop_details": [],
                    "redirect_404_details": [],
                    "redirect_unpublished_details": [],
                    "statistics": {},
                }
            )

        # Get broken link audit data
        from wagtail_seotoolkit.pro.models import BrokenLinkAuditResult

        # Get historical audit data for trend chart (both redirects and broken links)
        redirect_audits = RedirectAuditResult.objects.select_related(
            "audit_run"
        ).order_by("-created_at")[:15]

        broken_link_audits = BrokenLinkAuditResult.objects.select_related(
            "audit_run"
        ).order_by("-created_at")[:15]

        # Create a lookup for broken link audits by audit_run_id
        bl_audit_by_run = {bl.audit_run_id: bl for bl in broken_link_audits}

        chart_data = {
            "labels": [],
            "redirect_health_scores": [],
            "broken_link_health_scores": [],
            "combined_health_scores": [],
            "chains": [],
            "loops": [],
            "redirect_to_404": [],
            "broken_internal": [],
            "broken_external": [],
        }

        if redirect_audits:
            for audit in reversed(redirect_audits):
                chart_data["labels"].append(
                    audit.audit_run.created_at.strftime("%b %d, %Y")
                )
                chart_data["redirect_health_scores"].append(audit.health_score)
                chart_data["chains"].append(audit.chains_detected)
                chart_data["loops"].append(audit.circular_loops)
                chart_data["redirect_to_404"].append(audit.redirects_to_404)

                # Get corresponding broken link audit data
                bl_audit = bl_audit_by_run.get(audit.audit_run_id)
                if bl_audit:
                    chart_data["broken_link_health_scores"].append(
                        bl_audit.health_score
                    )
                    chart_data["broken_internal"].append(bl_audit.broken_internal_links)
                    chart_data["broken_external"].append(bl_audit.broken_external_links)
                    # Combined health score (average of both)
                    combined = (audit.health_score + bl_audit.health_score) // 2
                    chart_data["combined_health_scores"].append(combined)
                else:
                    chart_data["broken_link_health_scores"].append(None)
                    chart_data["broken_internal"].append(0)
                    chart_data["broken_external"].append(0)
                    chart_data["combined_health_scores"].append(audit.health_score)

        context["chart_data_json"] = json.dumps(chart_data)

        latest_broken_link_audit = None
        if latest_audit:
            try:
                latest_broken_link_audit = BrokenLinkAuditResult.objects.get(
                    audit_run=latest_audit
                )
            except BrokenLinkAuditResult.DoesNotExist:
                pass

        if latest_broken_link_audit:
            context.update(
                {
                    "has_broken_link_data": True,
                    "broken_link_audit": latest_broken_link_audit,
                    "bl_pages_scanned": latest_broken_link_audit.total_pages_scanned,
                    "bl_links_checked": latest_broken_link_audit.total_links_checked,
                    "bl_broken_internal": latest_broken_link_audit.broken_internal_links,
                    "bl_to_unpublished": latest_broken_link_audit.links_to_unpublished,
                    "bl_broken_external": latest_broken_link_audit.broken_external_links,
                    "bl_health_score": latest_broken_link_audit.health_score,
                    "bl_has_issues": latest_broken_link_audit.has_issues,
                    # Detailed broken link data
                    "bl_broken_internal_details": latest_broken_link_audit.audit_details.get(
                        "broken_internal_links", []
                    )[:10],
                    "bl_to_unpublished_details": latest_broken_link_audit.audit_details.get(
                        "links_to_unpublished", []
                    )[:10],
                    "bl_broken_external_details": latest_broken_link_audit.audit_details.get(
                        "broken_external_links", []
                    )[:10],
                }
            )
        else:
            context.update(
                {
                    "has_broken_link_data": False,
                    "broken_link_audit": None,
                    "bl_pages_scanned": 0,
                    "bl_links_checked": 0,
                    "bl_broken_internal": 0,
                    "bl_to_unpublished": 0,
                    "bl_broken_external": 0,
                    "bl_health_score": None,
                    "bl_has_issues": False,
                    "bl_broken_internal_details": [],
                    "bl_to_unpublished_details": [],
                    "bl_broken_external_details": [],
                }
            )

        # Calculate combined health score
        redirect_score = context.get("health_score")
        bl_score = context.get("bl_health_score")

        if redirect_score is not None and bl_score is not None:
            combined_health_score = (redirect_score + bl_score) // 2
        elif redirect_score is not None:
            combined_health_score = redirect_score
        elif bl_score is not None:
            combined_health_score = bl_score
        else:
            combined_health_score = None

        context["combined_health_score"] = combined_health_score

        # Check for subscription
        verification = PluginEmailVerification.objects.first()
        context["stored_email"] = verification.email if verification else None

        return context


# =============================================================================
# JSON-LD Schema Editor Views
# =============================================================================


class JSONLDSchemaListView(TemplateView):
    """
    View for listing all JSON-LD schema templates.
    """

    template_name = "wagtail_seotoolkit/jsonld/schema_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from wagtail_seotoolkit.pro.models import JSONLDSchemaTemplate

        # Get all schema templates
        templates = JSONLDSchemaTemplate.objects.all().select_related(
            "created_by", "content_type"
        )

        # Check subscription status
        verification = PluginEmailVerification.objects.first()
        email = verification.email if verification else None

        from wagtail_seotoolkit.pro.models import SubscriptionLicense

        license = SubscriptionLicense.objects.first()
        instance_id = str(license.instance_id) if license else None

        context.update(
            {
                "templates": templates,
                "page_title": _("JSON-LD Schema Templates"),
                "subscription_email": email,
                "subscription_instance_id": instance_id,
            }
        )

        return context


class JSONLDSchemaCreateView(TemplateView):
    """
    View for creating a new JSON-LD schema template.
    Uses Wagtail's StreamField UI for schema composition.
    """

    template_name = "wagtail_seotoolkit/jsonld/schema_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail_seotoolkit.pro.forms import JSONLDSchemaTemplateForm
        from wagtail_seotoolkit.pro.utils.jsonld_utils import (
            get_jsonld_placeholders_for_content_type,
        )

        # Get initial placeholders
        initial_placeholders = get_jsonld_placeholders_for_content_type(None)

        # Create the form for StreamField editing
        form = JSONLDSchemaTemplateForm()

        context.update(
            {
                "page_title": _("Create JSON-LD Schema Template"),
                "is_create": True,
                "form": form,
                "placeholders": initial_placeholders,
            }
        )

        return context

    def post(self, request):
        """Handle template creation"""
        from django.shortcuts import redirect

        from wagtail_seotoolkit.pro.forms import JSONLDSchemaTemplateForm

        form = JSONLDSchemaTemplateForm(request.POST)

        if form.is_valid():
            template = form.save(commit=False)
            if request.user.is_authenticated:
                template.created_by = request.user
            template.save()

            # For AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Template created successfully",
                        "template_id": template.id,
                        "redirect_url": f"/admin/seo-toolkit/jsonld-schemas/{template.id}/edit/",
                    }
                )
            return redirect("jsonld_schema_edit", template_id=template.id)
        else:
            # Return form with errors for re-rendering
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": str(form.errors)}, status=400
                )
            # Re-render template with form errors
            return self.render_to_response(self.get_context_data(form=form))


class JSONLDSchemaEditView(TemplateView):
    """
    View for editing an existing JSON-LD schema template.
    Renders the StreamField editor for schema composition.
    """

    template_name = "wagtail_seotoolkit/jsonld/schema_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail_seotoolkit.pro.forms import JSONLDSchemaTemplateForm
        from wagtail_seotoolkit.pro.models import JSONLDSchemaTemplate

        template_id = kwargs.get("template_id")
        form = kwargs.get("form")  # May be passed from post() on error

        try:
            template = JSONLDSchemaTemplate.objects.get(id=template_id)

            # Create form with instance if not already provided
            if form is None:
                form = JSONLDSchemaTemplateForm(instance=template)

            from wagtail_seotoolkit.pro.utils.jsonld_utils import (
                get_jsonld_placeholders_for_content_type,
            )

            # Get placeholders for current content type
            placeholders = get_jsonld_placeholders_for_content_type(
                template.content_type_id if template.content_type else None
            )

            context.update(
                {
                    "page_title": _("Edit JSON-LD Schema Template"),
                    "is_create": False,
                    "template": template,
                    "form": form,
                    "placeholders": placeholders,
                }
            )
        except JSONLDSchemaTemplate.DoesNotExist:
            context.update({"error": "Template not found"})

        return context

    def post(self, request, template_id):
        """Handle template update"""
        from django.shortcuts import redirect

        from wagtail_seotoolkit.pro.forms import JSONLDSchemaTemplateForm
        from wagtail_seotoolkit.pro.models import JSONLDSchemaTemplate

        try:
            template = JSONLDSchemaTemplate.objects.get(id=template_id)
        except JSONLDSchemaTemplate.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Template not found"}, status=404
                )
            return redirect("jsonld_schema_list")

        form = JSONLDSchemaTemplateForm(request.POST, instance=template)

        if form.is_valid():
            form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Template updated successfully"}
                )
            return redirect("jsonld_schema_list")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": str(form.errors)}, status=400
                )
            # Re-render template with form errors
            return self.render_to_response(
                self.get_context_data(template_id=template_id, form=form)
            )


class JSONLDSchemaDeleteView(View):
    """
    View for deleting a JSON-LD schema template.
    """

    def post(self, request, template_id):
        """Handle template deletion"""
        try:
            from wagtail_seotoolkit.pro.models import JSONLDSchemaTemplate

            template = JSONLDSchemaTemplate.objects.get(id=template_id)
            template_name = template.name
            template.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Template "{template_name}" deleted successfully',
                }
            )

        except JSONLDSchemaTemplate.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Template not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class SiteWideSchemaEditView(TemplateView):
    """
    View for editing site-wide JSON-LD schemas.
    One schema per site with StreamField for multiple schema types.
    Users have full control over schema construction using placeholders.
    """

    template_name = "wagtail_seotoolkit/jsonld/site_wide_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail.models import Site

        from wagtail_seotoolkit.pro.forms import SiteWideJSONLDSchemaForm
        from wagtail_seotoolkit.pro.models import SiteWideJSONLDSchema
        from wagtail_seotoolkit.pro.utils.jsonld_utils import get_site_wide_placeholders

        current_site = Site.find_for_request(self.request)
        form = kwargs.get("form")  # May be passed from post() on error

        # Get or create site-wide schema
        schema, created = SiteWideJSONLDSchema.objects.get_or_create(
            site=current_site,
            defaults={"is_active": True},
        )

        # Create form with instance if not already provided
        if form is None:
            form = SiteWideJSONLDSchemaForm(instance=schema)

        # Get placeholders for site-wide schemas
        placeholders = get_site_wide_placeholders()

        context.update(
            {
                "page_title": _("Site-Wide JSON-LD Schemas"),
                "current_site": current_site,
                "schema": schema,
                "form": form,
                "placeholders": placeholders,
            }
        )

        return context

    def post(self, request):
        """Handle site-wide schema updates"""
        from django.shortcuts import redirect
        from wagtail.models import Site

        from wagtail_seotoolkit.pro.forms import SiteWideJSONLDSchemaForm
        from wagtail_seotoolkit.pro.models import SiteWideJSONLDSchema

        current_site = Site.find_for_request(request)

        # Get or create schema
        schema, created = SiteWideJSONLDSchema.objects.get_or_create(
            site=current_site,
            defaults={"is_active": True},
        )

        form = SiteWideJSONLDSchemaForm(request.POST, instance=schema)

        if form.is_valid():
            form.save()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Site-wide schemas updated successfully",
                    }
                )
            return redirect("jsonld_site_wide")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": str(form.errors)}, status=400
                )
            # Re-render template with form errors
            return self.render_to_response(self.get_context_data(form=form))


class PageJSONLDEditView(TemplateView):
    """
    View for editing JSON-LD schema for a single page.
    Linked from the promote tab help panel.
    """

    template_name = "wagtail_seotoolkit/jsonld/page_schema_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from wagtail_seotoolkit.pro.forms import PageJSONLDOverrideForm
        from wagtail_seotoolkit.pro.models import (
            JSONLDSchemaTemplate,
            PageJSONLDOverride,
        )

        page_id = kwargs.get("page_id") or self.request.GET.get("page_id")
        form = kwargs.get("form")  # May be passed from post() on error

        try:
            page = Page.objects.get(id=page_id)
            page = page.specific

            # Get or create override for this page
            override = None
            try:
                override = PageJSONLDOverride.objects.get(page=page)
            except PageJSONLDOverride.DoesNotExist:
                pass

            # Create form with instance if not already provided
            if form is None:
                if override:
                    form = PageJSONLDOverrideForm(instance=override)
                else:
                    form = PageJSONLDOverrideForm()

            # Get available templates for this page type
            templates = JSONLDSchemaTemplate.objects.filter(is_active=True).filter(
                models.Q(content_type=page.content_type)
                | models.Q(content_type__isnull=True)
            )

            from wagtail_seotoolkit.pro.utils.jsonld_utils import (
                get_jsonld_placeholders_for_content_type,
            )

            placeholders = get_jsonld_placeholders_for_content_type(
                page.content_type_id
            )

            context.update(
                {
                    "page_title": _("Edit Page JSON-LD Schema"),
                    "page": page,
                    "override": override,
                    "form": form,
                    "available_templates": templates,
                    "placeholders": placeholders,
                }
            )
        except Page.DoesNotExist:
            context.update({"error": "Page not found"})

        return context

    def post(self, request, page_id):
        """Handle page override creation/update"""
        from django.shortcuts import redirect

        from wagtail_seotoolkit.pro.forms import PageJSONLDOverrideForm
        from wagtail_seotoolkit.pro.models import PageJSONLDOverride

        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Page not found"}, status=404
                )
            return redirect("jsonld_schema_list")

        # Get or create override
        try:
            override = PageJSONLDOverride.objects.get(page=page)
        except PageJSONLDOverride.DoesNotExist:
            override = PageJSONLDOverride(page=page)

        form = PageJSONLDOverrideForm(request.POST, instance=override)

        if form.is_valid():
            form.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Page schema override saved successfully",
                        "override_id": override.id,
                    }
                )
            return redirect("wagtailadmin_pages:edit", page.id)
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": str(form.errors)}, status=400
                )
            # Re-render template with form errors
            return self.render_to_response(
                self.get_context_data(page_id=page_id, form=form)
            )


def get_jsonld_schema_fields_api(request):
    """
    API endpoint to get available fields for a schema type.
    """
    from wagtail_seotoolkit.pro.utils.jsonld_schema_fields import get_schema_fields

    schema_type = request.GET.get("schema_type", "")

    if not schema_type:
        return JsonResponse(
            {"success": False, "error": "Schema type required"}, status=400
        )

    fields = get_schema_fields(schema_type)

    return JsonResponse({"success": True, "fields": fields})


def preview_jsonld_api(request):
    """
    API endpoint to preview generated JSON-LD for a page.
    """
    from wagtail_seotoolkit.pro.utils.jsonld_utils import (
        generate_jsonld_for_page,
        render_jsonld_script,
    )

    page_id = request.GET.get("page_id", "")

    if not page_id:
        return JsonResponse({"success": False, "error": "Page ID required"}, status=400)

    try:
        page = Page.objects.get(id=page_id)
        schemas = generate_jsonld_for_page(page, request)
        html = render_jsonld_script(schemas)

        return JsonResponse(
            {
                "success": True,
                "schemas": schemas,
                "html": html,
            }
        )
    except Page.DoesNotExist:
        return JsonResponse({"success": False, "error": "Page not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def get_jsonld_placeholders_api(request):
    """
    API endpoint to get available placeholders for a content type.
    """
    from wagtail_seotoolkit.pro.utils.jsonld_utils import (
        get_jsonld_placeholders_for_content_type,
    )

    content_type_id = request.GET.get("content_type_id")

    try:
        if content_type_id:
            content_type_id = int(content_type_id)
        else:
            content_type_id = None

        placeholders = get_jsonld_placeholders_for_content_type(content_type_id)

        return JsonResponse({"success": True, "placeholders": placeholders})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
