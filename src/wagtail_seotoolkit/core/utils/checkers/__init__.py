"""
SEO checker modules for modular SEO auditing.

Each checker module is responsible for a specific aspect of SEO auditing.
"""

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker
from wagtail_seotoolkit.core.utils.checkers.content_checker import ContentChecker
from wagtail_seotoolkit.core.utils.checkers.freshness_checker import FreshnessChecker
from wagtail_seotoolkit.core.utils.checkers.header_checker import HeaderChecker
from wagtail_seotoolkit.core.utils.checkers.image_checker import ImageChecker
from wagtail_seotoolkit.core.utils.checkers.link_checker import LinkChecker
from wagtail_seotoolkit.core.utils.checkers.meta_checker import MetaChecker
from wagtail_seotoolkit.core.utils.checkers.mobile_checker import MobileChecker
from wagtail_seotoolkit.core.utils.checkers.pagespeed_checker import PageSpeedChecker
from wagtail_seotoolkit.core.utils.checkers.placeholder_checker import (
    PlaceholderChecker,
)
from wagtail_seotoolkit.core.utils.checkers.schema_checker import SchemaChecker
from wagtail_seotoolkit.core.utils.checkers.title_checker import TitleChecker

__all__ = [
    "BaseChecker",
    "TitleChecker",
    "MetaChecker",
    "ContentChecker",
    "HeaderChecker",
    "ImageChecker",
    "SchemaChecker",
    "MobileChecker",
    "LinkChecker",
    "FreshnessChecker",
    "PageSpeedChecker",
    "PlaceholderChecker",
]
