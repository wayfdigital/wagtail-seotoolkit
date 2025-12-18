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

Licensed under the WAYF Proprietary License.
"""

from wagtail_seotoolkit.pro.blocks.jsonld_blocks import (
    # Supporting type blocks - E-commerce & Offers
    AggregateOfferBlock,
    AggregateRatingBlock,
    # Main schema blocks - Content
    ArticleSchemaBlock,
    # Main schema blocks - Media
    AudioObjectSchemaBlock,
    BlogPostingSchemaBlock,
    # Main schema blocks - Publishing
    BookSchemaBlock,
    # Supporting type blocks - Navigation
    BreadcrumbItemBlock,
    # Main schema blocks - Navigation & Lists
    BreadcrumbListSchemaBlock,
    # Supporting type blocks - Basic
    ContactPointBlock,
    # Supporting type blocks - Custom
    CustomNestedObjectBlock,
    CustomPropertyBlock,
    # Main schema blocks - Custom
    CustomSchemaBlock,
    # Main schema blocks - Events & Projects
    EventSchemaBlock,
    FAQItemBlock,
    FAQPageSchemaBlock,
    # Main schema blocks - HowTo & Instructions
    HowToSchemaBlock,
    # Supporting type blocks - HowTo
    HowToStepBlock,
    HowToSupplyBlock,
    HowToToolBlock,
    ImageObjectBlock,
    ItemListElementBlock,
    ItemListSchemaBlock,
    # Main schema blocks - Jobs
    JobPostingSchemaBlock,
    # Container blocks
    JSONLDSchemaFieldsBlock,
    JSONLDSchemasBlock,
    MediaObjectBlock,
    # Supporting type blocks - Food
    MenuItemBlock,
    # Main schema blocks - Food & Hospitality
    MenuSchemaBlock,
    MenuSectionBlock,
    MonetaryAmountBlock,
    # Main schema blocks - Location & Finance
    MonetaryGrantSchemaBlock,
    NewsArticleSchemaBlock,
    NutritionBlock,
    OfferBlock,
    OrganizationNestedBlock,
    # Main schema blocks - People & Organizations
    OrganizationSchemaBlock,
    PersonBlock,
    PersonSchemaBlock,
    PlaceBlock,
    PlaceSchemaBlock,
    PodcastEpisodeSchemaBlock,
    PodcastSeriesSchemaBlock,
    PostalAddressBlock,
    # Main schema blocks - Commerce & Products
    ProductSchemaBlock,
    ProfilePageSchemaBlock,
    ProjectSchemaBlock,
    RecipeInstructionBlock,
    RecipeSchemaBlock,
    ReportSchemaBlock,
    RestaurantSchemaBlock,
    ReviewItemBlock,
    # Main schema blocks - Reviews
    ReviewSchemaBlock,
    ScholarlyArticleSchemaBlock,
    ServiceSchemaBlock,
    # Site-wide schema blocks
    SiteLocalBusinessBlock,
    SiteOrganizationBlock,
    SiteWebSiteBlock,
    SiteWideSchemasBlock,
    SoftwareApplicationSchemaBlock,
    SpeakableSpecificationBlock,
    VideoObjectSchemaBlock,
    WebPageSchemaBlock,
)

__all__ = [
    # Supporting type blocks - Basic
    "PersonBlock",
    "ImageObjectBlock",
    "PostalAddressBlock",
    "ContactPointBlock",
    "OrganizationNestedBlock",
    "SpeakableSpecificationBlock",
    "FAQItemBlock",
    "MonetaryAmountBlock",
    "PlaceBlock",
    "MediaObjectBlock",
    "CustomPropertyBlock",
    "NutritionBlock",
    "RecipeInstructionBlock",
    # Supporting type blocks - E-commerce & Offers
    "OfferBlock",
    "AggregateOfferBlock",
    "AggregateRatingBlock",
    "ReviewItemBlock",
    # Supporting type blocks - HowTo
    "HowToStepBlock",
    "HowToSupplyBlock",
    "HowToToolBlock",
    # Supporting type blocks - Navigation
    "BreadcrumbItemBlock",
    "ItemListElementBlock",
    # Supporting type blocks - Food
    "MenuItemBlock",
    "MenuSectionBlock",
    # Supporting type blocks - Custom
    "CustomNestedObjectBlock",
    # Main schema blocks - Content
    "ArticleSchemaBlock",
    "BlogPostingSchemaBlock",
    "NewsArticleSchemaBlock",
    "ReportSchemaBlock",
    "ScholarlyArticleSchemaBlock",
    "FAQPageSchemaBlock",
    "WebPageSchemaBlock",
    # Main schema blocks - Commerce & Products
    "ProductSchemaBlock",
    "ServiceSchemaBlock",
    "SoftwareApplicationSchemaBlock",
    # Main schema blocks - Jobs
    "JobPostingSchemaBlock",
    # Main schema blocks - HowTo & Instructions
    "HowToSchemaBlock",
    "RecipeSchemaBlock",
    # Main schema blocks - Media
    "VideoObjectSchemaBlock",
    "AudioObjectSchemaBlock",
    "PodcastSeriesSchemaBlock",
    "PodcastEpisodeSchemaBlock",
    # Main schema blocks - Reviews
    "ReviewSchemaBlock",
    # Main schema blocks - People & Organizations
    "OrganizationSchemaBlock",
    "PersonSchemaBlock",
    "ProfilePageSchemaBlock",
    # Main schema blocks - Events & Projects
    "EventSchemaBlock",
    "ProjectSchemaBlock",
    # Main schema blocks - Food & Hospitality
    "RestaurantSchemaBlock",
    "MenuSchemaBlock",
    # Main schema blocks - Navigation & Lists
    "BreadcrumbListSchemaBlock",
    "ItemListSchemaBlock",
    # Main schema blocks - Publishing
    "BookSchemaBlock",
    # Main schema blocks - Location & Finance
    "PlaceSchemaBlock",
    "MonetaryGrantSchemaBlock",
    # Main schema blocks - Custom
    "CustomSchemaBlock",
    # Site-wide schema blocks
    "SiteOrganizationBlock",
    "SiteWebSiteBlock",
    "SiteLocalBusinessBlock",
    "SiteWideSchemasBlock",
    # Container blocks
    "JSONLDSchemaFieldsBlock",
    "JSONLDSchemasBlock",
]
