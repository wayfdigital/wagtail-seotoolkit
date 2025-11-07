# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
Subscription helper functions - Pro Feature

These functions help check subscription status and manage instances.
All subscription checks go through the external API (never stored locally).

Caching behavior:
- Production (DEBUG=False): Only Pro subscription responses are cached for 24 hours
- Free/non-Pro responses are never cached (immediate feedback on upgrades)
- Development (DEBUG=True): Caching is completely disabled for testing

Licensed under the WAYF Proprietary License.
"""

import requests
from django.core.cache import cache

API_BASE_URL = "https://wagtail-seotoolkit-license-server.vercel.app"


def check_subscription_active(email, instance_id):
    """
    Check if subscription is active for given email and instance.

    Caching: Only Pro responses are cached (24 hours) in production.
    Non-Pro responses are never cached for immediate upgrade feedback.

    Args:
        email: User's email address
        instance_id: UUID of this Wagtail instance

    Returns:
        bool: True if subscription is active and instance is registered
    """
    from django.conf import settings

    if not email or not instance_id:
        return False

    # Skip caching in DEBUG mode for development
    use_cache = not getattr(settings, "DEBUG", False)

    # Check cache first - only if not in DEBUG mode
    # Note: Only Pro responses are cached, so this will only return cached Pro status
    cache_key = f"subscription:{email}:{instance_id}"
    if use_cache:
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data.get("pro", False)

    try:
        # Call external API
        response = requests.get(
            f"{API_BASE_URL}/api/check-subscription",
            params={"email": email, "instanceId": str(instance_id)},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            is_pro = data.get("pro", False)

            # Cache ONLY Pro responses for 24 hours in production
            # Non-Pro responses are never cached so users see upgrades immediately
            if use_cache and is_pro is True:
                cache.set(cache_key, data, 86400)

            return is_pro

        return False

    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False


def get_or_create_instance_id():
    """
    Get existing instance ID or create new one.

    Returns:
        UUID: Instance ID for this Wagtail installation
    """
    from ..models import SubscriptionLicense

    license = SubscriptionLicense.objects.first()

    if license:
        return license.instance_id

    # No license exists yet, will be created when user adds email
    return None


def get_subscription_data(email, instance_id):
    """
    Get full subscription data from API.

    Caching: Only Pro responses are cached (24 hours) in production.
    Non-Pro responses are never cached for immediate upgrade feedback.

    Args:
        email: User's email address
        instance_id: UUID of this Wagtail instance

    Returns:
        dict: Subscription data including tier, status, expires, etc.
        None: If no subscription or error
    """
    from django.conf import settings

    if not email or not instance_id:
        return None

    # Skip caching in DEBUG mode for development
    use_cache = not getattr(settings, "DEBUG", False)

    # Check cache first - only if not in DEBUG mode
    # Note: Only Pro responses are cached, so this will only return cached Pro data
    cache_key = f"subscription:{email}:{instance_id}"
    if use_cache:
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/check-subscription",
            params={"email": email, "instanceId": str(instance_id)},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            # Cache ONLY Pro responses for 24 hours in production
            # Non-Pro responses are never cached so users see upgrades immediately
            if use_cache and data.get("pro") is True:
                cache.set(cache_key, data, 86400)

            return data

        return None

    except Exception as e:
        print(f"Error getting subscription data: {e}")
        return None


def ensure_instance_registered(email, instance_id, site_url=""):
    """
    Ensure this instance is registered to the subscription.

    Calls the register-instance API endpoint.
    Safe to call multiple times (idempotent).

    Args:
        email: User's email address
        instance_id: UUID of this Wagtail instance
        site_url: Optional site URL

    Returns:
        tuple: (success: bool, message: str)
    """
    if not email or not instance_id:
        return False, "Email and instance ID are required"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register-instance",
            json={
                "email": email,
                "instanceId": str(instance_id),
                "siteUrl": site_url,
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if response.status_code == 200:
            # Clear cache to force fresh check
            cache_key = f"subscription:{email}:{instance_id}"
            cache.delete(cache_key)

            return True, data.get("message", "Instance registered successfully")

        return False, data.get("error", "Failed to register instance")

    except Exception as e:
        return False, f"Error registering instance: {str(e)}"


def get_available_plans():
    """
    Get available subscription plans from license server.

    Returns:
        dict: Plans data with pricing and features
        None: If error occurred
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/get-plans",
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"Error getting plans: {e}")
        return None


def clear_subscription_cache(email, instance_id):
    """
    Clear cached subscription data.

    Useful after subscription changes (cancel, downgrade, etc.)
    Note: Only Pro responses are cached, so this mainly affects downgrades/cancellations.
    Cache is automatically disabled in DEBUG mode.

    Args:
        email: User's email address
        instance_id: UUID of this Wagtail instance
    """
    from django.conf import settings

    # Cache clearing is a no-op in DEBUG mode since caching is disabled
    if getattr(settings, "DEBUG", False):
        return

    cache_key = f"subscription:{email}:{instance_id}"
    cache.delete(cache_key)


def list_instances(email):
    """
    Get list of all registered instances for an email.

    Args:
        email: User's email address

    Returns:
        dict: Instance data including list, counts, and seat info
        None: If error occurred
    """
    if not email:
        return None

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/list-instances",
            params={"email": email},
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"Error listing instances: {e}")
        return None


def get_active_instances(email):
    """
    Get list of active instances for an email.

    Args:
        email: User's email address

    Returns:
        dict: Active instances data with status
        None: If error occurred
    """
    if not email:
        return None

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/get-active-instances",
            params={"email": email},
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"Error getting active instances: {e}")
        return None


def set_active_instances(email, instance_ids):
    """
    Set which instances should be active (have pro access).

    Args:
        email: User's email address
        instance_ids: List of instance ID strings to activate

    Returns:
        tuple: (success: bool, message: str, data: dict)
    """
    if not email:
        return False, "Email is required", None

    if not isinstance(instance_ids, list):
        return False, "instance_ids must be a list", None

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/set-active-instances",
            json={"email": email, "instanceIds": instance_ids},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if response.status_code == 200:
            # Clear all caches for this email since active instances changed
            # In production, we can't easily clear all instance caches,
            # but they will refresh on next check
            return True, data.get("message", "Active instances updated"), data

        return False, data.get("error", "Failed to set active instances"), data

    except Exception as e:
        return False, f"Error setting active instances: {str(e)}", None


def clear_active_instances(email):
    """
    Clear all active instances for an email (deactivate all).

    Args:
        email: User's email address

    Returns:
        tuple: (success: bool, message: str)
    """
    if not email:
        return False, "Email is required"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/clear-active-instances",
            json={"email": email},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if response.status_code == 200:
            return True, data.get("message", "All instances deactivated")

        return False, data.get("error", "Failed to clear active instances")

    except Exception as e:
        return False, f"Error clearing active instances: {str(e)}"


def remove_instance(email, instance_id):
    """
    Remove an instance from the registered instances list.

    Args:
        email: User's email address
        instance_id: UUID of the instance to remove

    Returns:
        tuple: (success: bool, message: str)
    """
    if not email or not instance_id:
        return False, "Email and instance ID are required"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/remove-instance",
            json={"email": email, "instanceId": str(instance_id)},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        data = response.json()

        if response.status_code == 200:
            # Clear cache for this specific instance
            cache_key = f"subscription:{email}:{instance_id}"
            cache.delete(cache_key)

            return True, data.get("message", "Instance removed successfully")

        return False, data.get("error", "Failed to remove instance")

    except Exception as e:
        return False, f"Error removing instance: {str(e)}"
