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
