# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
StreamField blocks for JSON-LD schema composition.

These blocks allow users to compose JSON-LD structured data schemas
using Wagtail's native StreamField UI (rendered via Telepath).

Licensed under the WAYF Proprietary License.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

# =============================================================================
# Supporting Type Blocks (nested within main schema blocks)
# =============================================================================


class PersonBlock(blocks.StructBlock):
    """
    Person schema block for author, creator, contributor fields.
    Supports placeholders like {author_name} for dynamic values.
    """

    name = blocks.CharBlock(
        required=False,
        help_text=_("Person name or {field} placeholder (e.g., {author_name})"),
    )
    url = blocks.CharBlock(
        required=False,
        help_text=_("Profile URL or {field} placeholder"),
    )
    image = blocks.CharBlock(
        required=False,
        help_text=_("Image URL or {field} placeholder (e.g., {author_image})"),
    )
    job_title = blocks.CharBlock(
        required=False,
        label=_("Job Title"),
        help_text=_("Job title or {field} placeholder"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social/Profile URLs"),
        help_text=_("Links to social media profiles or other URLs"),
    )

    class Meta:
        icon = "user"
        label = _("Person")


class ImageObjectBlock(blocks.StructBlock):
    """
    ImageObject schema block for image properties.
    Supports placeholders for dynamic image URLs.
    """

    url = blocks.CharBlock(
        required=False,
        help_text=_("Image URL or {field} placeholder (e.g., {header_image})"),
    )
    width = blocks.IntegerBlock(
        required=False,
        help_text=_("Image width in pixels"),
    )
    height = blocks.IntegerBlock(
        required=False,
        help_text=_("Image height in pixels"),
    )
    caption = blocks.CharBlock(
        required=False,
        help_text=_("Image caption or {field} placeholder"),
    )

    class Meta:
        icon = "image"
        label = _("Image")


class PostalAddressBlock(blocks.StructBlock):
    """
    PostalAddress schema block for physical addresses.
    """

    street_address = blocks.CharBlock(
        required=False,
        label=_("Street Address"),
    )
    address_locality = blocks.CharBlock(
        required=False,
        label=_("City"),
    )
    address_region = blocks.CharBlock(
        required=False,
        label=_("State/Region"),
    )
    postal_code = blocks.CharBlock(
        required=False,
        label=_("Postal Code"),
    )
    address_country = blocks.CharBlock(
        required=False,
        label=_("Country"),
    )

    class Meta:
        icon = "site"
        label = _("Address")


class ContactPointBlock(blocks.StructBlock):
    """
    ContactPoint schema block for contact information.
    """

    telephone = blocks.CharBlock(
        required=False,
        help_text=_("Phone number"),
    )
    email = blocks.EmailBlock(
        required=False,
        help_text=_("Email address"),
    )
    contact_type = blocks.CharBlock(
        required=False,
        label=_("Contact Type"),
        help_text=_("e.g., customer service, sales, technical support"),
    )
    available_language = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Available Languages"),
        help_text=_("Languages supported (e.g., English, Spanish)"),
    )

    class Meta:
        icon = "mail"
        label = _("Contact Point")


class OrganizationNestedBlock(blocks.StructBlock):
    """
    Simplified Organization block for nesting within other schemas.
    Used for publisher, worksFor, etc.
    """

    name = blocks.CharBlock(
        required=False,
        help_text=_("Organization name or {site_name} placeholder"),
    )
    url = blocks.CharBlock(
        required=False,
        help_text=_("Organization URL"),
    )
    logo = blocks.CharBlock(
        required=False,
        help_text=_("Logo URL or {field} placeholder"),
    )

    class Meta:
        icon = "group"
        label = _("Publisher/Organization")


class SpeakableSpecificationBlock(blocks.StructBlock):
    """
    SpeakableSpecification for voice search optimization.
    Defines which parts of the page are suitable for text-to-speech.
    """

    css_selector = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("CSS Selectors"),
        help_text=_("CSS selectors for speakable content (e.g., .article-body, h1)"),
    )
    xpath = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("XPath Expressions"),
        help_text=_("XPath expressions for speakable content"),
    )

    class Meta:
        icon = "openquote"
        label = _("Speakable Specification")


class FAQItemBlock(blocks.StructBlock):
    """
    FAQ Question/Answer pair for FAQPage schema.
    """

    question = blocks.CharBlock(
        required=False,
        help_text=_("Question text or {field} placeholder"),
    )
    answer = blocks.TextBlock(
        required=False,
        help_text=_("Answer text or {field} placeholder"),
    )

    class Meta:
        icon = "help"
        label = _("FAQ Item")


class MonetaryAmountBlock(blocks.StructBlock):
    """
    MonetaryAmount for financial schemas (grants, loans, etc.).
    """

    value = blocks.CharBlock(
        required=False,
        help_text=_("Amount value or {field} placeholder"),
    )
    currency = blocks.CharBlock(
        required=False,
        default="USD",
        help_text=_("Currency code (e.g., USD, EUR, GBP)"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Monetary Amount")


class PlaceBlock(blocks.StructBlock):
    """
    Place schema for locations.
    """

    name = blocks.CharBlock(
        required=False,
        help_text=_("Place name or {field} placeholder"),
    )
    address = PostalAddressBlock(required=False)
    geo_latitude = blocks.DecimalBlock(
        required=False,
        label=_("Latitude"),
    )
    geo_longitude = blocks.DecimalBlock(
        required=False,
        label=_("Longitude"),
    )

    class Meta:
        icon = "site"
        label = _("Place")


class MediaObjectBlock(blocks.StructBlock):
    """
    MediaObject for PDF/document encodings.
    """

    content_url = blocks.CharBlock(
        required=False,
        label=_("Content URL"),
        help_text=_("URL to the media file or {field} placeholder"),
    )
    encoding_format = blocks.CharBlock(
        required=False,
        label=_("Format"),
        help_text=_("MIME type (e.g., application/pdf, video/mp4)"),
    )
    name = blocks.CharBlock(
        required=False,
        help_text=_("Media name or {field} placeholder"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Media Object")


class CustomPropertyBlock(blocks.StructBlock):
    """
    Generic property block for flexible field mapping.
    Allows users to add any schema.org property not covered by specific blocks.
    """

    property_name = blocks.CharBlock(
        required=False,
        label=_("Property Name"),
        help_text=_("Schema.org property (e.g., wordCount, inLanguage)"),
    )
    value = blocks.CharBlock(
        required=False,
        help_text=_(
            "Static value or {field} placeholder (e.g., {title}, {first_published_at})"
        ),
    )

    class Meta:
        icon = "code"
        label = _("Custom Property")


# =============================================================================
# E-commerce & Offer Blocks
# =============================================================================


class OfferBlock(blocks.StructBlock):
    """
    Offer schema for product pricing and availability.
    Used within Product, Service, and other commerce schemas.
    """

    price = blocks.CharBlock(
        required=False,
        help_text=_("Price value or {field} placeholder"),
    )
    price_currency = blocks.CharBlock(
        required=False,
        default="USD",
        label=_("Currency"),
        help_text=_("Currency code (e.g., USD, EUR, GBP)"),
    )
    availability = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("InStock", "In Stock"),
            ("OutOfStock", "Out of Stock"),
            ("PreOrder", "Pre-Order"),
            ("BackOrder", "Back Order"),
            ("SoldOut", "Sold Out"),
            ("OnlineOnly", "Online Only"),
            ("LimitedAvailability", "Limited Availability"),
            ("Discontinued", "Discontinued"),
        ],
        required=False,
        help_text=_("Product availability status"),
    )
    url = blocks.CharBlock(
        required=False,
        help_text=_("URL where the offer can be acquired"),
    )
    valid_from = blocks.CharBlock(
        required=False,
        label=_("Valid From"),
        help_text=_("Date when offer becomes valid (ISO 8601)"),
    )
    price_valid_until = blocks.CharBlock(
        required=False,
        label=_("Price Valid Until"),
        help_text=_("Date when price expires (ISO 8601)"),
    )
    item_condition = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("NewCondition", "New"),
            ("UsedCondition", "Used"),
            ("RefurbishedCondition", "Refurbished"),
            ("DamagedCondition", "Damaged"),
        ],
        required=False,
        label=_("Item Condition"),
        help_text=_("Condition of the item being offered"),
    )

    class Meta:
        icon = "tag"
        label = _("Offer")


class AggregateOfferBlock(blocks.StructBlock):
    """
    AggregateOffer schema for price ranges from multiple sellers.
    """

    low_price = blocks.CharBlock(
        required=False,
        label=_("Lowest Price"),
        help_text=_("Lowest price among all offers"),
    )
    high_price = blocks.CharBlock(
        required=False,
        label=_("Highest Price"),
        help_text=_("Highest price among all offers"),
    )
    offer_count = blocks.IntegerBlock(
        required=False,
        label=_("Number of Offers"),
        help_text=_("Total number of offers available"),
    )
    price_currency = blocks.CharBlock(
        required=False,
        default="USD",
        label=_("Currency"),
        help_text=_("Currency code (e.g., USD, EUR, GBP)"),
    )

    class Meta:
        icon = "tag"
        label = _("Aggregate Offer")


# =============================================================================
# Review & Rating Blocks
# =============================================================================


class AggregateRatingBlock(blocks.StructBlock):
    """
    AggregateRating schema for star ratings summary.
    """

    rating_value = blocks.CharBlock(
        required=False,
        label=_("Rating Value"),
        help_text=_("Average rating value or {field} placeholder"),
    )
    best_rating = blocks.CharBlock(
        required=False,
        default="5",
        label=_("Best Rating"),
        help_text=_("Highest possible rating (default: 5)"),
    )
    worst_rating = blocks.CharBlock(
        required=False,
        default="1",
        label=_("Worst Rating"),
        help_text=_("Lowest possible rating (default: 1)"),
    )
    rating_count = blocks.CharBlock(
        required=False,
        label=_("Rating Count"),
        help_text=_("Number of ratings"),
    )
    review_count = blocks.CharBlock(
        required=False,
        label=_("Review Count"),
        help_text=_("Number of reviews"),
    )

    class Meta:
        icon = "pick"
        label = _("Aggregate Rating")


class ReviewItemBlock(blocks.StructBlock):
    """
    Individual review for use within Review schema or embedded in other schemas.
    """

    author = PersonBlock(required=False, label=_("Reviewer"))
    review_rating = blocks.CharBlock(
        required=False,
        label=_("Rating"),
        help_text=_("Rating value (e.g., 4.5)"),
    )
    review_body = blocks.TextBlock(
        required=False,
        label=_("Review Text"),
        help_text=_("The review content"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {field} placeholder"),
    )

    class Meta:
        icon = "openquote"
        label = _("Review")


# =============================================================================
# HowTo Instruction Blocks
# =============================================================================


class HowToStepBlock(blocks.StructBlock):
    """
    Single step in a HowTo guide.
    """

    name = blocks.CharBlock(
        required=False,
        label=_("Step Name"),
        help_text=_("Brief name for this step"),
    )
    text = blocks.TextBlock(
        required=True,
        help_text=_("Detailed instructions for this step"),
    )
    image = ImageObjectBlock(required=False, label=_("Step Image"))
    url = blocks.CharBlock(
        required=False,
        help_text=_("URL to a page with more details about this step"),
    )

    class Meta:
        icon = "list-ol"
        label = _("How-To Step")


class HowToSupplyBlock(blocks.StructBlock):
    """
    Supply/material needed for a HowTo guide.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Name of the supply or material"),
    )
    image = blocks.CharBlock(
        required=False,
        help_text=_("Image URL of the supply"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Supply")


class HowToToolBlock(blocks.StructBlock):
    """
    Tool needed for a HowTo guide.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Name of the tool"),
    )
    image = blocks.CharBlock(
        required=False,
        help_text=_("Image URL of the tool"),
    )

    class Meta:
        icon = "cog"
        label = _("Tool")


# =============================================================================
# Navigation & Breadcrumb Blocks
# =============================================================================


class BreadcrumbItemBlock(blocks.StructBlock):
    """
    Single item in a breadcrumb trail.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Display name for this breadcrumb item"),
    )
    url = blocks.CharBlock(
        required=True,
        help_text=_("URL of the breadcrumb item"),
    )

    class Meta:
        icon = "link"
        label = _("Breadcrumb Item")


class ItemListElementBlock(blocks.StructBlock):
    """
    Single item in an ItemList (for carousels).
    """

    name = blocks.CharBlock(
        required=False,
        help_text=_("Item name or {field} placeholder"),
    )
    url = blocks.CharBlock(
        required=True,
        help_text=_("URL of the list item"),
    )
    image = blocks.CharBlock(
        required=False,
        help_text=_("Image URL or {field} placeholder"),
    )

    class Meta:
        icon = "list-ul"
        label = _("List Item")


# =============================================================================
# Food & Restaurant Blocks
# =============================================================================


class MenuItemBlock(blocks.StructBlock):
    """
    Single menu item for a restaurant menu.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Name of the menu item"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Description of the menu item"),
    )
    price = blocks.CharBlock(
        required=False,
        help_text=_("Price of the item"),
    )
    price_currency = blocks.CharBlock(
        required=False,
        default="USD",
        label=_("Currency"),
    )
    image = blocks.CharBlock(
        required=False,
        help_text=_("Image URL of the menu item"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Menu Item")


class MenuSectionBlock(blocks.StructBlock):
    """
    Section of a restaurant menu (e.g., Appetizers, Main Course).
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Section name (e.g., Appetizers, Desserts)"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Section description"),
    )
    has_menu_item = blocks.ListBlock(
        MenuItemBlock(),
        required=False,
        label=_("Menu Items"),
        help_text=_("Items in this menu section"),
    )

    class Meta:
        icon = "list-ul"
        label = _("Menu Section")


# =============================================================================
# Main Schema Type Blocks (top-level schemas)
# =============================================================================


class ArticleSchemaBlock(blocks.StructBlock):
    """
    Article schema - base for all article types.
    Can be used for generic articles.
    """

    headline = blocks.CharBlock(
        required=True,
        help_text=_("Article headline or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Article description or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    date_modified = blocks.CharBlock(
        required=False,
        label=_("Date Modified"),
        help_text=_("ISO 8601 date or {last_published_at} placeholder"),
    )
    author = PersonBlock(required=False, label=_("Author"))
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    image = ImageObjectBlock(required=False, label=_("Main Image"))
    speakable = SpeakableSpecificationBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Article")
        template = None


class BlogPostingSchemaBlock(blocks.StructBlock):
    """
    BlogPosting schema for blog posts.
    Extends Article with blog-specific properties.
    """

    headline = blocks.CharBlock(
        required=True,
        help_text=_("Blog post headline or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Post description or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    date_modified = blocks.CharBlock(
        required=False,
        label=_("Date Modified"),
        help_text=_("ISO 8601 date or {last_published_at} placeholder"),
    )
    author = PersonBlock(required=False, label=_("Author"))
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    image = ImageObjectBlock(required=False, label=_("Main Image"))
    word_count = blocks.CharBlock(
        required=False,
        label=_("Word Count"),
        help_text=_("Word count or {word_count} placeholder"),
    )
    speakable = SpeakableSpecificationBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "edit"
        label = _("Blog Posting")


class NewsArticleSchemaBlock(blocks.StructBlock):
    """
    NewsArticle schema for news content.
    """

    headline = blocks.CharBlock(
        required=True,
        help_text=_("News headline or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("News description or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    date_modified = blocks.CharBlock(
        required=False,
        label=_("Date Modified"),
        help_text=_("ISO 8601 date or {last_published_at} placeholder"),
    )
    author = PersonBlock(required=False, label=_("Author"))
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    image = ImageObjectBlock(required=False, label=_("Main Image"))
    dateline = blocks.CharBlock(
        required=False,
        help_text=_("Location and date line (e.g., 'NEW YORK, Dec 1')"),
    )
    speakable = SpeakableSpecificationBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "globe"
        label = _("News Article")


class ReportSchemaBlock(blocks.StructBlock):
    """
    Report schema for reports and publications.
    """

    headline = blocks.CharBlock(
        required=True,
        help_text=_("Report title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Report description or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    author = PersonBlock(required=False, label=_("Author"))
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    encoding = MediaObjectBlock(
        required=False,
        label=_("PDF/Document"),
        help_text=_("Link to downloadable PDF version"),
    )
    speakable = SpeakableSpecificationBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "doc-full-inverse"
        label = _("Report")


class ScholarlyArticleSchemaBlock(blocks.StructBlock):
    """
    ScholarlyArticle schema for academic content.
    """

    headline = blocks.CharBlock(
        required=True,
        help_text=_("Article title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Abstract or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
    )
    author = blocks.ListBlock(
        PersonBlock(),
        required=False,
        label=_("Authors"),
        help_text=_("Add multiple authors"),
    )
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    encoding = MediaObjectBlock(required=False, label=_("PDF/Document"))
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "clipboard-list"
        label = _("Scholarly Article")


class FAQPageSchemaBlock(blocks.StructBlock):
    """
    FAQPage schema for FAQ pages.
    """

    main_entity = blocks.ListBlock(
        FAQItemBlock(),
        required=True,
        label=_("FAQ Items"),
        help_text=_("Add question/answer pairs"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "help"
        label = _("FAQ Page")


class OrganizationSchemaBlock(blocks.StructBlock):
    """
    Organization schema for organization pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Organization name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Organization description"),
    )
    url = blocks.CharBlock(
        required=False,
        help_text=_("Organization URL"),
    )
    logo = blocks.CharBlock(
        required=False,
        help_text=_("Logo URL or {field} placeholder"),
    )
    address = PostalAddressBlock(required=False)
    contact_point = blocks.ListBlock(
        ContactPointBlock(),
        required=False,
        label=_("Contact Points"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social/Profile URLs"),
        help_text=_("Links to social media profiles"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "group"
        label = _("Organization")


class PersonSchemaBlock(blocks.StructBlock):
    """
    Person schema for profile/biography pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Person name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Biography or description"),
    )
    job_title = blocks.CharBlock(
        required=False,
        label=_("Job Title"),
    )
    image = ImageObjectBlock(required=False, label=_("Photo"))
    works_for = OrganizationNestedBlock(
        required=False,
        label=_("Works For"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social/Profile URLs"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "user"
        label = _("Person")


class PlaceSchemaBlock(blocks.StructBlock):
    """
    Place/Country schema for location pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Place name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
    )
    address = PostalAddressBlock(required=False)
    geo_latitude = blocks.DecimalBlock(
        required=False,
        label=_("Latitude"),
    )
    geo_longitude = blocks.DecimalBlock(
        required=False,
        label=_("Longitude"),
    )
    image = ImageObjectBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "site"
        label = _("Place/Country")


class MonetaryGrantSchemaBlock(blocks.StructBlock):
    """
    MonetaryGrant schema for grant/funding pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Grant name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
    )
    amount = MonetaryAmountBlock(required=False, label=_("Grant Amount"))
    funder = OrganizationNestedBlock(required=False, label=_("Funder"))
    funded_item = blocks.CharBlock(
        required=False,
        label=_("Funded Item"),
        help_text=_("Project or item being funded"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Monetary Grant")


class ProjectSchemaBlock(blocks.StructBlock):
    """
    Project schema for project pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Project name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
    )
    start_date = blocks.CharBlock(
        required=False,
        label=_("Start Date"),
    )
    end_date = blocks.CharBlock(
        required=False,
        label=_("End Date"),
    )
    funder = OrganizationNestedBlock(required=False, label=_("Funder"))
    location = PlaceBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "folder-open-inverse"
        label = _("Project")


class WebPageSchemaBlock(blocks.StructBlock):
    """
    Generic WebPage schema.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Page name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Page description or {search_description} placeholder"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
    )
    date_modified = blocks.CharBlock(
        required=False,
        label=_("Date Modified"),
    )
    speakable = SpeakableSpecificationBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "doc-empty"
        label = _("Web Page")


class EventSchemaBlock(blocks.StructBlock):
    """
    Event schema for event pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Event name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
    )
    start_date = blocks.CharBlock(
        required=False,
        label=_("Start Date/Time"),
        help_text=_("ISO 8601 format or {field} placeholder"),
    )
    end_date = blocks.CharBlock(
        required=False,
        label=_("End Date/Time"),
    )
    location = PlaceBlock(required=False)
    organizer = OrganizationNestedBlock(required=False)
    image = ImageObjectBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "date"
        label = _("Event")


class RecipeInstructionBlock(blocks.StructBlock):
    """
    Single instruction step for a recipe.
    """

    text = blocks.TextBlock(
        required=False,
        help_text=_("Instruction step text"),
    )

    class Meta:
        icon = "list-ol"
        label = _("Instruction Step")


class NutritionBlock(blocks.StructBlock):
    """
    Nutrition information for a recipe.
    """

    calories = blocks.CharBlock(
        required=False,
        help_text=_("Calories (e.g., '250 calories')"),
    )
    fat_content = blocks.CharBlock(
        required=False,
        label=_("Fat"),
        help_text=_("Fat content (e.g., '12 g')"),
    )
    carbohydrate_content = blocks.CharBlock(
        required=False,
        label=_("Carbohydrates"),
        help_text=_("Carbohydrate content (e.g., '30 g')"),
    )
    protein_content = blocks.CharBlock(
        required=False,
        label=_("Protein"),
        help_text=_("Protein content (e.g., '15 g')"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Nutrition Information")


class RecipeSchemaBlock(blocks.StructBlock):
    """
    Recipe schema for recipe pages.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Recipe name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Recipe description or {search_description} placeholder"),
    )
    image = ImageObjectBlock(required=False, label=_("Recipe Image"))
    author = PersonBlock(required=False, label=_("Author"))
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    prep_time = blocks.CharBlock(
        required=False,
        label=_("Prep Time"),
        help_text=_("ISO 8601 duration (e.g., PT15M for 15 minutes)"),
    )
    cook_time = blocks.CharBlock(
        required=False,
        label=_("Cook Time"),
        help_text=_("ISO 8601 duration (e.g., PT1H for 1 hour)"),
    )
    total_time = blocks.CharBlock(
        required=False,
        label=_("Total Time"),
        help_text=_("ISO 8601 duration (e.g., PT1H15M)"),
    )
    recipe_yield = blocks.CharBlock(
        required=False,
        label=_("Yield/Servings"),
        help_text=_("Number of servings (e.g., '4 servings')"),
    )
    recipe_category = blocks.CharBlock(
        required=False,
        label=_("Category"),
        help_text=_("Recipe category (e.g., Dessert, Main Course, Appetizer)"),
    )
    recipe_cuisine = blocks.CharBlock(
        required=False,
        label=_("Cuisine"),
        help_text=_("Cuisine type (e.g., Italian, Mexican, American)"),
    )
    recipe_ingredient = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Ingredients"),
        help_text=_("List of ingredients"),
    )
    recipe_instructions = blocks.ListBlock(
        RecipeInstructionBlock(),
        required=False,
        label=_("Instructions"),
        help_text=_("Step-by-step instructions"),
    )
    nutrition = NutritionBlock(required=False, label=_("Nutrition Information"))
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "snippet"
        label = _("Recipe")


class ProductSchemaBlock(blocks.StructBlock):
    """
    Product schema for product pages.
    Enables product rich results with pricing, availability, and reviews.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Product name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Product description"),
    )
    image = ImageObjectBlock(required=False, label=_("Product Image"))
    brand = blocks.CharBlock(
        required=False,
        help_text=_("Brand name or {field} placeholder"),
    )
    sku = blocks.CharBlock(
        required=False,
        label=_("SKU"),
        help_text=_("Stock Keeping Unit identifier"),
    )
    gtin = blocks.CharBlock(
        required=False,
        label=_("GTIN"),
        help_text=_("Global Trade Item Number (GTIN-8, GTIN-12, GTIN-13, or GTIN-14)"),
    )
    mpn = blocks.CharBlock(
        required=False,
        label=_("MPN"),
        help_text=_("Manufacturer Part Number"),
    )
    offers = OfferBlock(
        required=False,
        label=_("Offer"),
        help_text=_("Product pricing and availability"),
    )
    aggregate_offer = AggregateOfferBlock(
        required=False,
        label=_("Aggregate Offer"),
        help_text=_("Price range when multiple offers exist"),
    )
    aggregate_rating = AggregateRatingBlock(
        required=False,
        label=_("Rating"),
        help_text=_("Overall product rating"),
    )
    review = blocks.ListBlock(
        ReviewItemBlock(),
        required=False,
        label=_("Reviews"),
        help_text=_("Individual product reviews"),
    )
    category = blocks.CharBlock(
        required=False,
        help_text=_("Product category"),
    )
    color = blocks.CharBlock(
        required=False,
        help_text=_("Product color"),
    )
    material = blocks.CharBlock(
        required=False,
        help_text=_("Product material"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "pick"
        label = _("Product")


# =============================================================================
# HowTo & Instructions Schema Blocks
# =============================================================================


class HowToSchemaBlock(blocks.StructBlock):
    """
    HowTo schema for step-by-step guides and tutorials.
    Enables rich results showing steps in Google Search.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Title of the how-to guide or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Description of what this guide teaches"),
    )
    image = ImageObjectBlock(required=False, label=_("Main Image"))
    total_time = blocks.CharBlock(
        required=False,
        label=_("Total Time"),
        help_text=_("ISO 8601 duration (e.g., PT30M for 30 minutes, PT2H for 2 hours)"),
    )
    estimated_cost = MonetaryAmountBlock(
        required=False,
        label=_("Estimated Cost"),
        help_text=_("Estimated cost to complete this guide"),
    )
    supply = blocks.ListBlock(
        HowToSupplyBlock(),
        required=False,
        label=_("Supplies"),
        help_text=_("Materials needed for this guide"),
    )
    tool = blocks.ListBlock(
        HowToToolBlock(),
        required=False,
        label=_("Tools"),
        help_text=_("Tools needed for this guide"),
    )
    step = blocks.ListBlock(
        HowToStepBlock(),
        required=True,
        label=_("Steps"),
        help_text=_("Step-by-step instructions"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "list-ol"
        label = _("How-To Guide")


# =============================================================================
# Media Schema Blocks (Video, Audio, Podcast)
# =============================================================================


class VideoObjectSchemaBlock(blocks.StructBlock):
    """
    VideoObject schema for video content.
    Enables video rich results and video carousels in Google Search.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Video title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Video description or {search_description} placeholder"),
    )
    thumbnail_url = blocks.CharBlock(
        required=True,
        label=_("Thumbnail URL"),
        help_text=_("URL of the video thumbnail image"),
    )
    upload_date = blocks.CharBlock(
        required=False,
        label=_("Upload Date"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    duration = blocks.CharBlock(
        required=False,
        help_text=_("ISO 8601 duration (e.g., PT5M30S for 5 min 30 sec)"),
    )
    content_url = blocks.CharBlock(
        required=False,
        label=_("Content URL"),
        help_text=_("Direct URL to the video file"),
    )
    embed_url = blocks.CharBlock(
        required=False,
        label=_("Embed URL"),
        help_text=_("URL of the embeddable player (e.g., YouTube embed URL)"),
    )
    transcript = blocks.TextBlock(
        required=False,
        help_text=_("Video transcript text"),
    )
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "media"
        label = _("Video")


class AudioObjectSchemaBlock(blocks.StructBlock):
    """
    AudioObject schema for audio content.
    Used for podcast episodes, music, and other audio files.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Audio title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Audio description"),
    )
    content_url = blocks.CharBlock(
        required=True,
        label=_("Content URL"),
        help_text=_("Direct URL to the audio file"),
    )
    duration = blocks.CharBlock(
        required=False,
        help_text=_("ISO 8601 duration (e.g., PT45M for 45 minutes)"),
    )
    encoding_format = blocks.CharBlock(
        required=False,
        label=_("Format"),
        help_text=_("MIME type (e.g., audio/mpeg, audio/ogg)"),
    )
    transcript = blocks.TextBlock(
        required=False,
        help_text=_("Audio transcript text"),
    )
    upload_date = blocks.CharBlock(
        required=False,
        label=_("Upload Date"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "media"
        label = _("Audio")


class PodcastSeriesSchemaBlock(blocks.StructBlock):
    """
    PodcastSeries schema for podcast shows.
    Helps search engines understand podcast content.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Podcast name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Podcast description"),
    )
    image = ImageObjectBlock(required=False, label=_("Podcast Artwork"))
    author = PersonBlock(required=False, label=_("Host/Author"))
    publisher = OrganizationNestedBlock(required=False, label=_("Publisher"))
    url = blocks.CharBlock(
        required=False,
        help_text=_("Podcast homepage URL"),
    )
    web_feed = blocks.CharBlock(
        required=False,
        label=_("RSS Feed URL"),
        help_text=_("URL of the podcast RSS feed"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "media"
        label = _("Podcast Series")


class PodcastEpisodeSchemaBlock(blocks.StructBlock):
    """
    PodcastEpisode schema for individual podcast episodes.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Episode title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Episode description"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    duration = blocks.CharBlock(
        required=False,
        help_text=_("ISO 8601 duration (e.g., PT1H15M for 1 hour 15 minutes)"),
    )
    episode_number = blocks.IntegerBlock(
        required=False,
        label=_("Episode Number"),
    )
    season_number = blocks.IntegerBlock(
        required=False,
        label=_("Season Number"),
    )
    audio = blocks.CharBlock(
        required=False,
        label=_("Audio URL"),
        help_text=_("Direct URL to the episode audio file"),
    )
    part_of_series = blocks.CharBlock(
        required=False,
        label=_("Series Name"),
        help_text=_("Name of the podcast series this belongs to"),
    )
    image = ImageObjectBlock(required=False, label=_("Episode Artwork"))
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "media"
        label = _("Podcast Episode")


# =============================================================================
# Commerce & Service Schema Blocks
# =============================================================================


class ServiceSchemaBlock(blocks.StructBlock):
    """
    Service schema for service offerings.
    Describes intangible services provided by organizations.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Service name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Service description"),
    )
    service_type = blocks.CharBlock(
        required=False,
        label=_("Service Type"),
        help_text=_("Type of service (e.g., Consulting, Web Development)"),
    )
    provider = OrganizationNestedBlock(
        required=False,
        label=_("Provider"),
        help_text=_("Organization providing this service"),
    )
    area_served = blocks.CharBlock(
        required=False,
        label=_("Area Served"),
        help_text=_("Geographic area where service is available"),
    )
    offers = OfferBlock(
        required=False,
        label=_("Pricing"),
        help_text=_("Service pricing and availability"),
    )
    aggregate_rating = AggregateRatingBlock(
        required=False,
        label=_("Rating"),
    )
    image = ImageObjectBlock(required=False)
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "cog"
        label = _("Service")


class SoftwareApplicationSchemaBlock(blocks.StructBlock):
    """
    SoftwareApplication schema for software and apps.
    Enables rich results for software in Google Search.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Application name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Application description"),
    )
    application_category = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("BusinessApplication", "Business Application"),
            ("BrowserApplication", "Browser Application"),
            ("CommunicationApplication", "Communication Application"),
            ("DeveloperApplication", "Developer Application"),
            ("EducationApplication", "Education Application"),
            ("EntertainmentApplication", "Entertainment Application"),
            ("FinanceApplication", "Finance Application"),
            ("GameApplication", "Game Application"),
            ("HealthApplication", "Health Application"),
            ("LifestyleApplication", "Lifestyle Application"),
            ("MediaApplication", "Media Application"),
            ("MusicApplication", "Music Application"),
            ("NavigationApplication", "Navigation Application"),
            ("NewsApplication", "News Application"),
            ("PhotoApplication", "Photo Application"),
            ("ProductivityApplication", "Productivity Application"),
            ("ReferenceApplication", "Reference Application"),
            ("SecurityApplication", "Security Application"),
            ("ShoppingApplication", "Shopping Application"),
            ("SocialNetworkingApplication", "Social Networking Application"),
            ("SportsApplication", "Sports Application"),
            ("TravelApplication", "Travel Application"),
            ("UtilitiesApplication", "Utilities Application"),
            ("WeatherApplication", "Weather Application"),
        ],
        required=False,
        label=_("Category"),
        help_text=_("Application category"),
    )
    operating_system = blocks.CharBlock(
        required=False,
        label=_("Operating System"),
        help_text=_("e.g., Windows 10, macOS, iOS, Android"),
    )
    software_version = blocks.CharBlock(
        required=False,
        label=_("Version"),
        help_text=_("Software version number"),
    )
    offers = OfferBlock(
        required=False,
        label=_("Pricing"),
    )
    aggregate_rating = AggregateRatingBlock(
        required=False,
        label=_("Rating"),
    )
    image = ImageObjectBlock(required=False, label=_("App Icon/Screenshot"))
    download_url = blocks.CharBlock(
        required=False,
        label=_("Download URL"),
        help_text=_("URL to download the application"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "cog"
        label = _("Software Application")


class JobPostingSchemaBlock(blocks.StructBlock):
    """
    JobPosting schema for job listings.
    Enables job posting rich results in Google Search.
    """

    title = blocks.CharBlock(
        required=True,
        help_text=_("Job title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=True,
        help_text=_("Full job description with responsibilities"),
    )
    date_posted = blocks.CharBlock(
        required=False,
        label=_("Date Posted"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    valid_through = blocks.CharBlock(
        required=False,
        label=_("Valid Through"),
        help_text=_("Application deadline (ISO 8601 date)"),
    )
    employment_type = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("FULL_TIME", "Full Time"),
            ("PART_TIME", "Part Time"),
            ("CONTRACTOR", "Contractor"),
            ("TEMPORARY", "Temporary"),
            ("INTERN", "Intern"),
            ("VOLUNTEER", "Volunteer"),
            ("PER_DIEM", "Per Diem"),
            ("OTHER", "Other"),
        ],
        required=False,
        label=_("Employment Type"),
    )
    hiring_organization = OrganizationNestedBlock(
        required=False,
        label=_("Hiring Organization"),
    )
    job_location = PlaceBlock(
        required=False,
        label=_("Job Location"),
    )
    job_location_type = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("TELECOMMUTE", "Remote/Telecommute"),
        ],
        required=False,
        label=_("Location Type"),
        help_text=_("Select if this is a remote position"),
    )
    base_salary = MonetaryAmountBlock(
        required=False,
        label=_("Base Salary"),
    )
    salary_unit = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("HOUR", "Per Hour"),
            ("DAY", "Per Day"),
            ("WEEK", "Per Week"),
            ("MONTH", "Per Month"),
            ("YEAR", "Per Year"),
        ],
        required=False,
        label=_("Salary Unit"),
    )
    qualifications = blocks.TextBlock(
        required=False,
        help_text=_("Required qualifications and skills"),
    )
    responsibilities = blocks.TextBlock(
        required=False,
        help_text=_("Job responsibilities"),
    )
    benefits = blocks.TextBlock(
        required=False,
        label=_("Benefits"),
        help_text=_("Job benefits and perks"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "user"
        label = _("Job Posting")


# =============================================================================
# E-E-A-T & Authority Schema Blocks
# =============================================================================


class ProfilePageSchemaBlock(blocks.StructBlock):
    """
    ProfilePage schema for author/creator profile pages.
    Important for E-E-A-T (Experience, Expertise, Authoritativeness, Trust).
    """

    date_created = blocks.CharBlock(
        required=False,
        label=_("Date Created"),
        help_text=_("When the profile was created (ISO 8601)"),
    )
    date_modified = blocks.CharBlock(
        required=False,
        label=_("Date Modified"),
        help_text=_("When the profile was last updated (ISO 8601)"),
    )
    main_entity_name = blocks.CharBlock(
        required=True,
        label=_("Person Name"),
        help_text=_("Name of the person or {title} placeholder"),
    )
    main_entity_job_title = blocks.CharBlock(
        required=False,
        label=_("Job Title"),
        help_text=_("Professional title"),
    )
    main_entity_description = blocks.TextBlock(
        required=False,
        label=_("Biography"),
        help_text=_("Biography or professional description"),
    )
    main_entity_image = blocks.CharBlock(
        required=False,
        label=_("Profile Image URL"),
        help_text=_("URL to profile photo"),
    )
    main_entity_url = blocks.CharBlock(
        required=False,
        label=_("Profile URL"),
        help_text=_("Canonical URL of this profile page"),
    )
    works_for = OrganizationNestedBlock(
        required=False,
        label=_("Works For"),
        help_text=_("Organization the person works for"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social/Profile URLs"),
        help_text=_("Links to social media profiles (LinkedIn, Twitter, etc.)"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "user"
        label = _("Profile Page")


class ReviewSchemaBlock(blocks.StructBlock):
    """
    Review schema for individual reviews.
    Can be used for product reviews, service reviews, etc.
    """

    item_reviewed_type = blocks.ChoiceBlock(
        choices=[
            ("Product", "Product"),
            ("Service", "Service"),
            ("LocalBusiness", "Local Business"),
            ("Organization", "Organization"),
            ("Book", "Book"),
            ("Movie", "Movie"),
            ("Restaurant", "Restaurant"),
            ("SoftwareApplication", "Software Application"),
            ("Event", "Event"),
            ("CreativeWork", "Creative Work"),
            ("Thing", "Other"),
        ],
        required=False,
        label=_("Item Type"),
        help_text=_("What type of item is being reviewed"),
    )
    item_reviewed_name = blocks.CharBlock(
        required=True,
        label=_("Item Name"),
        help_text=_("Name of the item being reviewed"),
    )
    item_reviewed_url = blocks.CharBlock(
        required=False,
        label=_("Item URL"),
        help_text=_("URL of the item being reviewed"),
    )
    author = PersonBlock(
        required=False,
        label=_("Reviewer"),
        help_text=_("Person who wrote the review"),
    )
    review_rating = blocks.CharBlock(
        required=False,
        label=_("Rating"),
        help_text=_("Rating value (e.g., 4.5)"),
    )
    best_rating = blocks.CharBlock(
        required=False,
        default="5",
        label=_("Best Rating"),
        help_text=_("Maximum possible rating"),
    )
    worst_rating = blocks.CharBlock(
        required=False,
        default="1",
        label=_("Worst Rating"),
        help_text=_("Minimum possible rating"),
    )
    review_body = blocks.TextBlock(
        required=False,
        label=_("Review Text"),
        help_text=_("The full review content"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("ISO 8601 date or {first_published_at} placeholder"),
    )
    publisher = OrganizationNestedBlock(
        required=False,
        label=_("Publisher"),
        help_text=_("Organization that published the review"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "openquote"
        label = _("Review")


# =============================================================================
# Publishing Schema Blocks
# =============================================================================


class BookSchemaBlock(blocks.StructBlock):
    """
    Book schema for book pages.
    Provides rich information about books.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Book title or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Book description or synopsis"),
    )
    author = blocks.ListBlock(
        PersonBlock(),
        required=False,
        label=_("Authors"),
        help_text=_("Book author(s)"),
    )
    isbn = blocks.CharBlock(
        required=False,
        label=_("ISBN"),
        help_text=_("ISBN-13 or ISBN-10"),
    )
    book_edition = blocks.CharBlock(
        required=False,
        label=_("Edition"),
        help_text=_("Book edition (e.g., First Edition, 2nd Edition)"),
    )
    book_format = blocks.ChoiceBlock(
        choices=[
            ("", "Not specified"),
            ("Hardcover", "Hardcover"),
            ("Paperback", "Paperback"),
            ("EBook", "E-Book"),
            ("AudiobookFormat", "Audiobook"),
        ],
        required=False,
        label=_("Format"),
    )
    number_of_pages = blocks.IntegerBlock(
        required=False,
        label=_("Number of Pages"),
    )
    publisher = OrganizationNestedBlock(
        required=False,
        label=_("Publisher"),
    )
    date_published = blocks.CharBlock(
        required=False,
        label=_("Date Published"),
        help_text=_("Publication date (ISO 8601)"),
    )
    in_language = blocks.CharBlock(
        required=False,
        label=_("Language"),
        help_text=_("Language code (e.g., en, es, fr)"),
    )
    image = ImageObjectBlock(required=False, label=_("Book Cover"))
    aggregate_rating = AggregateRatingBlock(required=False, label=_("Rating"))
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "doc-full"
        label = _("Book")


# =============================================================================
# Food & Hospitality Schema Blocks
# =============================================================================


class RestaurantSchemaBlock(blocks.StructBlock):
    """
    Restaurant schema for restaurant pages.
    Extends LocalBusiness with food-specific properties.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Restaurant name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Restaurant description"),
    )
    image = ImageObjectBlock(required=False, label=_("Restaurant Image"))
    address = PostalAddressBlock(required=False)
    telephone = blocks.CharBlock(
        required=False,
        help_text=_("Restaurant phone number"),
    )
    url = blocks.CharBlock(
        required=False,
        help_text=_("Restaurant website URL"),
    )
    serves_cuisine = blocks.CharBlock(
        required=False,
        label=_("Cuisine"),
        help_text=_("Type of cuisine (e.g., Italian, Mexican, Japanese)"),
    )
    price_range = blocks.CharBlock(
        required=False,
        label=_("Price Range"),
        help_text=_("Price range indicator (e.g., $$, $$$)"),
    )
    opening_hours = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Opening Hours"),
        help_text=_("Opening hours in schema.org format (e.g., Mo-Fr 11:00-22:00)"),
    )
    accepts_reservations = blocks.BooleanBlock(
        required=False,
        label=_("Accepts Reservations"),
        help_text=_("Whether the restaurant accepts reservations"),
    )
    menu_url = blocks.CharBlock(
        required=False,
        label=_("Menu URL"),
        help_text=_("URL to the restaurant's menu"),
    )
    geo_latitude = blocks.DecimalBlock(
        required=False,
        label=_("Latitude"),
    )
    geo_longitude = blocks.DecimalBlock(
        required=False,
        label=_("Longitude"),
    )
    aggregate_rating = AggregateRatingBlock(required=False, label=_("Rating"))
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social Media URLs"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "home"
        label = _("Restaurant")


class MenuSchemaBlock(blocks.StructBlock):
    """
    Menu schema for restaurant menus.
    Provides structured menu information for search engines.
    """

    name = blocks.CharBlock(
        required=True,
        help_text=_("Menu name (e.g., Lunch Menu, Dinner Menu)"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("Menu description"),
    )
    has_menu_section = blocks.ListBlock(
        MenuSectionBlock(),
        required=False,
        label=_("Menu Sections"),
        help_text=_("Sections of the menu (e.g., Appetizers, Main Course, Desserts)"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "list-ul"
        label = _("Menu")


# =============================================================================
# Navigation & Collection Schema Blocks
# =============================================================================


class BreadcrumbListSchemaBlock(blocks.StructBlock):
    """
    BreadcrumbList schema for site navigation breadcrumbs.
    Helps search engines understand site structure.
    Note: Often auto-generated based on page hierarchy.
    """

    items = blocks.ListBlock(
        BreadcrumbItemBlock(),
        required=True,
        label=_("Breadcrumb Items"),
        help_text=_("Breadcrumb trail items in order from home to current page"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "link"
        label = _("Breadcrumb List")


class ItemListSchemaBlock(blocks.StructBlock):
    """
    ItemList schema for lists and carousels.
    Enables carousel rich results in Google Search.
    """

    name = blocks.CharBlock(
        required=False,
        help_text=_("List name or {title} placeholder"),
    )
    description = blocks.TextBlock(
        required=False,
        help_text=_("List description"),
    )
    item_list_order = blocks.ChoiceBlock(
        choices=[
            ("", "Unordered"),
            ("ItemListOrderAscending", "Ascending"),
            ("ItemListOrderDescending", "Descending"),
        ],
        required=False,
        label=_("List Order"),
        help_text=_("How items in the list are ordered"),
    )
    item_list_element = blocks.ListBlock(
        ItemListElementBlock(),
        required=True,
        label=_("List Items"),
        help_text=_("Items in the list (minimum 3 recommended for carousels)"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "list-ul"
        label = _("Item List")


# =============================================================================
# Custom Schema Block (Build Your Own)
# =============================================================================


class CustomNestedObjectBlock(blocks.StructBlock):
    """
    Nested object for custom schemas.
    Allows building complex nested structures.
    """

    property_name = blocks.CharBlock(
        required=False,
        label=_("Property Name"),
        help_text=_(
            "The property name where this object will be placed "
            "(e.g., offers, performer, location, author)"
        ),
    )
    object_type = blocks.CharBlock(
        required=False,
        label=_("@type"),
        help_text=_("Schema.org type for this object (e.g., Offer, Person, Place)"),
    )
    properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Properties"),
        help_text=_("Add properties for this nested object"),
    )

    class Meta:
        icon = "code"
        label = _("Nested Object")


class CustomSchemaBlock(blocks.StructBlock):
    """
    Custom schema block for building any schema.org type from scratch.
    Use this when predefined schema blocks don't meet your needs.
    Provides complete flexibility with no pre-defined fields.
    """

    schema_type = blocks.CharBlock(
        required=True,
        label=_("Schema Type (@type)"),
        help_text=_(
            "The schema.org type (e.g., Course, MusicEvent, MedicalClinic). "
            "See schema.org for all available types."
        ),
    )
    properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Properties"),
        help_text=_(
            "Add schema.org properties. Use property names exactly as shown on schema.org "
            "(e.g., name, description, startDate, endDate, performer). "
            "Values can include {placeholders} like {title}, {first_published_at}."
        ),
    )
    nested_objects = blocks.ListBlock(
        CustomNestedObjectBlock(),
        required=False,
        label=_("Nested Objects"),
        help_text=_(
            "Add complex nested objects with their own @type and properties "
            "(e.g., Offer with price, Person as performer, Place as location)."
        ),
    )

    class Meta:
        icon = "code"
        label = _("Custom Schema")


# =============================================================================
# Main StreamBlock containing all schema types
# =============================================================================


class JSONLDSchemasBlock(blocks.StreamBlock):
    """
    Main StreamBlock for composing JSON-LD schemas.
    Each block represents a complete schema type.
    Multiple schemas can be added to a single template.
    Blocks are organized into groups for better UX.
    """

    # ==========================================================================
    # COMMON (ungrouped - appear first in the picker menu)
    # ==========================================================================
    article = ArticleSchemaBlock()
    blog_posting = BlogPostingSchemaBlock()
    web_page = WebPageSchemaBlock()
    faq_page = FAQPageSchemaBlock()

    # ==========================================================================
    # COMMERCE & PRODUCTS
    # ==========================================================================
    product = ProductSchemaBlock(group=_("Commerce & Products"))
    service = ServiceSchemaBlock(group=_("Commerce & Products"))
    software_app = SoftwareApplicationSchemaBlock(group=_("Commerce & Products"))

    # ==========================================================================
    # JOBS & CAREERS
    # ==========================================================================
    job_posting = JobPostingSchemaBlock(group=_("Jobs & Careers"))

    # ==========================================================================
    # HOW-TO & INSTRUCTIONS
    # ==========================================================================
    how_to = HowToSchemaBlock(group=_("How-to & Instructions"))
    recipe = RecipeSchemaBlock(group=_("How-to & Instructions"))

    # ==========================================================================
    # MEDIA & CONTENT
    # ==========================================================================
    video = VideoObjectSchemaBlock(group=_("Media & Content"))
    audio = AudioObjectSchemaBlock(group=_("Media & Content"))
    podcast_series = PodcastSeriesSchemaBlock(group=_("Media & Content"))
    podcast_episode = PodcastEpisodeSchemaBlock(group=_("Media & Content"))
    book = BookSchemaBlock(group=_("Media & Content"))

    # ==========================================================================
    # REVIEWS & RATINGS
    # ==========================================================================
    review = ReviewSchemaBlock(group=_("Reviews & Ratings"))

    # ==========================================================================
    # PEOPLE & ORGANIZATIONS
    # ==========================================================================
    organization = OrganizationSchemaBlock(group=_("People & Organizations"))
    person = PersonSchemaBlock(group=_("People & Organizations"))
    profile_page = ProfilePageSchemaBlock(group=_("People & Organizations"))

    # ==========================================================================
    # EVENTS & PROJECTS
    # ==========================================================================
    event = EventSchemaBlock(group=_("Events & Projects"))
    project = ProjectSchemaBlock(group=_("Events & Projects"))

    # ==========================================================================
    # FOOD & HOSPITALITY
    # ==========================================================================
    restaurant = RestaurantSchemaBlock(group=_("Food & Hospitality"))
    menu = MenuSchemaBlock(group=_("Food & Hospitality"))

    # ==========================================================================
    # NAVIGATION & LISTS
    # ==========================================================================
    breadcrumb_list = BreadcrumbListSchemaBlock(group=_("Navigation & Lists"))
    item_list = ItemListSchemaBlock(group=_("Navigation & Lists"))

    # ==========================================================================
    # NEWS & PUBLISHING
    # ==========================================================================
    news_article = NewsArticleSchemaBlock(group=_("News & Publishing"))
    report = ReportSchemaBlock(group=_("News & Publishing"))
    scholarly_article = ScholarlyArticleSchemaBlock(group=_("News & Publishing"))

    # ==========================================================================
    # LOCATION & FINANCE
    # ==========================================================================
    place = PlaceSchemaBlock(group=_("Location & Finance"))
    monetary_grant = MonetaryGrantSchemaBlock(group=_("Location & Finance"))

    # ==========================================================================
    # CUSTOM (Build Your Own)
    # ==========================================================================
    custom_schema = CustomSchemaBlock(group=_("Custom"))

    class Meta:
        icon = "code"
        label = _("JSON-LD Schemas")


# =============================================================================
# Site-Wide Schema Blocks
# =============================================================================


class SiteOrganizationBlock(blocks.StructBlock):
    """
    Organization schema for site-wide use.
    Name and URL are auto-populated from Site settings.
    """

    description = blocks.TextBlock(
        required=False,
        help_text=_("Organization description"),
    )
    logo = blocks.CharBlock(
        required=False,
        help_text=_("Logo URL"),
    )
    address = PostalAddressBlock(required=False)
    contact_point = blocks.ListBlock(
        ContactPointBlock(),
        required=False,
        label=_("Contact Points"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social Media URLs"),
        help_text=_(
            "Links to social media profiles (Facebook, Twitter, LinkedIn, etc.)"
        ),
    )
    founding_date = blocks.CharBlock(
        required=False,
        label=_("Founding Date"),
        help_text=_("Year or date founded (e.g., 1990 or 1990-01-15)"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "group"
        label = _("Organization")


class SiteWebSiteBlock(blocks.StructBlock):
    """
    WebSite schema for site-wide use.
    Name and URL are auto-populated from Site settings.
    """

    description = blocks.TextBlock(
        required=False,
        help_text=_("Website description"),
    )
    publisher = OrganizationNestedBlock(
        required=False,
        label=_("Publisher"),
        help_text=_("Organization that publishes this website"),
    )
    potential_action_search = blocks.BooleanBlock(
        required=False,
        default=True,
        label=_("Enable Search Action"),
        help_text=_("Add SearchAction for site search functionality"),
    )
    search_url_template = blocks.CharBlock(
        required=False,
        label=_("Search URL Template"),
        help_text=_(
            "Search URL with {search_term_string} placeholder (e.g., /search/?q={search_term_string})"
        ),
        default="/search/?q={search_term_string}",
    )
    in_language = blocks.CharBlock(
        required=False,
        label=_("Language"),
        help_text=_("Primary language code (e.g., en, en-US, de)"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "globe"
        label = _("WebSite")


class SiteLocalBusinessBlock(blocks.StructBlock):
    """
    LocalBusiness schema for site-wide use.
    Name and URL are auto-populated from Site settings.
    """

    description = blocks.TextBlock(
        required=False,
        help_text=_("Business description"),
    )
    image = ImageObjectBlock(required=False, label=_("Business Image"))
    address = PostalAddressBlock(required=False, label=_("Business Address"))
    telephone = blocks.CharBlock(
        required=False,
        help_text=_("Business phone number"),
    )
    email = blocks.EmailBlock(
        required=False,
        help_text=_("Business email"),
    )
    price_range = blocks.CharBlock(
        required=False,
        label=_("Price Range"),
        help_text=_("Price range indicator (e.g., $$, $$$, €€)"),
    )
    opening_hours = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Opening Hours"),
        help_text=_("Opening hours in schema.org format (e.g., Mo-Fr 09:00-17:00)"),
    )
    geo_latitude = blocks.DecimalBlock(
        required=False,
        label=_("Latitude"),
    )
    geo_longitude = blocks.DecimalBlock(
        required=False,
        label=_("Longitude"),
    )
    same_as = blocks.ListBlock(
        blocks.CharBlock(required=False),
        required=False,
        label=_("Social Media URLs"),
    )
    additional_properties = blocks.ListBlock(
        CustomPropertyBlock(),
        required=False,
        label=_("Additional Properties"),
    )

    class Meta:
        icon = "home"
        label = _("Local Business")


class SiteWideSchemasBlock(blocks.StreamBlock):
    """
    StreamBlock for site-wide schemas.
    Name and URL are auto-populated from Wagtail Site settings.
    """

    organization = SiteOrganizationBlock()
    website = SiteWebSiteBlock()
    local_business = SiteLocalBusinessBlock()

    class Meta:
        icon = "site"
        label = _("Site-Wide Schemas")


# Legacy block kept for backwards compatibility
class JSONLDSchemaFieldsBlock(blocks.StreamBlock):
    """
    StreamBlock for additional fields in site-wide schemas.
    DEPRECATED: Use SiteWideSchemasBlock instead.
    """

    property = CustomPropertyBlock()
    image = ImageObjectBlock()
    address = PostalAddressBlock()
    contact_point = ContactPointBlock()
    person = PersonBlock()

    class Meta:
        icon = "code"
        label = _("Additional Schema Fields")
