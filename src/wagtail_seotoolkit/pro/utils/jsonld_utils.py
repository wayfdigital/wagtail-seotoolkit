# Copyright (C) 2025 WAYF DIGITAL SP. Z O.O. All rights reserved.
#
# This file is part of Wagtail SEO Toolkit Pro and is licensed under the
# WAYF Proprietary License. See LICENSE-PROPRIETARY in the project root.
#
# Usage is allowed only with a valid subscription. Modification and
# redistribution are prohibited without explicit permission from WAYF.
# For permissions: hello@wayfdigital.com

"""
JSON-LD processing utilities.

Functions for generating and processing JSON-LD structured data
from schema templates and page content.

Licensed under the WAYF Proprietary License.
"""

import json

from django.conf import settings

from wagtail_seotoolkit.pro.utils.placeholder_utils import process_placeholders


def streamfield_to_jsonld(stream_value, page, request=None):
    """
    Convert a StreamField value to JSON-LD structure.

    Processes each block in the StreamField and converts it to the
    appropriate JSON-LD property format, replacing placeholders with
    actual page values.

    Args:
        stream_value: StreamField value (list of blocks)
        page: Wagtail Page instance for placeholder processing
        request: Optional request for site-specific values

    Returns:
        Dict of JSON-LD properties
    """
    result = {}

    if not stream_value:
        return result

    for block in stream_value:
        block_type = block.block_type
        block_value = block.value

        if block_type == "property":
            # Custom property block
            prop_name = block_value.get("property_name", "")
            prop_value = block_value.get("value", "")
            if prop_name and prop_value:
                processed_value = process_placeholders(prop_value, page, request)
                result[prop_name] = processed_value

        elif block_type == "person":
            # Person block with property_name selector
            person_data = _process_person_block(block_value, page, request)
            if person_data:
                # Get the property name from the block (author, creator, contributor)
                prop_name = block_value.get("property_name", "author")
                # Handle repeatable fields
                if prop_name in result:
                    if isinstance(result[prop_name], list):
                        result[prop_name].append(person_data)
                    else:
                        result[prop_name] = [result[prop_name], person_data]
                else:
                    result[prop_name] = person_data

        elif block_type == "publisher":
            # Organization block
            org_data = _process_organization_block(block_value, page, request)
            if org_data:
                result["publisher"] = org_data

        elif block_type == "image":
            # ImageObject block
            image_data = _process_image_block(block_value, page, request)
            if image_data:
                if "image" in result:
                    if isinstance(result["image"], list):
                        result["image"].append(image_data)
                    else:
                        result["image"] = [result["image"], image_data]
                else:
                    result["image"] = image_data

        elif block_type == "address":
            # PostalAddress block
            address_data = _process_address_block(block_value, page, request)
            if address_data:
                result["address"] = address_data

        elif block_type == "contact_point":
            # ContactPoint block
            contact_data = _process_contact_point_block(block_value, page, request)
            if contact_data:
                if "contactPoint" in result:
                    if isinstance(result["contactPoint"], list):
                        result["contactPoint"].append(contact_data)
                    else:
                        result["contactPoint"] = [result["contactPoint"], contact_data]
                else:
                    result["contactPoint"] = contact_data

        elif block_type == "speakable":
            # SpeakableSpecification block
            speakable_data = _process_speakable_block(block_value)
            if speakable_data:
                result["speakable"] = speakable_data

        elif block_type == "faq_item":
            # FAQ Question/Answer block
            faq_data = _process_faq_item_block(block_value, page, request)
            if faq_data:
                if "mainEntity" not in result:
                    result["mainEntity"] = []
                result["mainEntity"].append(faq_data)

        elif block_type == "monetary_amount":
            # MonetaryAmount block
            amount_data = _process_monetary_amount_block(block_value, page, request)
            if amount_data:
                result["amount"] = amount_data

        elif block_type == "location":
            # Place block
            place_data = _process_place_block(block_value, page, request)
            if place_data:
                result["location"] = place_data

    return result


def _process_person_block(block_value, page, request):
    """Process a Person block into JSON-LD format."""
    person = {"@type": "Person"}

    name = block_value.get("name", "")
    if name:
        person["name"] = process_placeholders(name, page, request)

    url = block_value.get("url", "")
    if url:
        person["url"] = process_placeholders(url, page, request)

    image = block_value.get("image", "")
    if image:
        person["image"] = process_placeholders(image, page, request)

    job_title = block_value.get("job_title", "")
    if job_title:
        person["jobTitle"] = process_placeholders(job_title, page, request)

    same_as = block_value.get("same_as", [])
    if same_as:
        person["sameAs"] = list(same_as)

    return person if len(person) > 1 else None


def _process_organization_block(block_value, page, request):
    """Process an Organization block into JSON-LD format."""
    org = {"@type": "Organization"}

    name = block_value.get("name", "")
    if name:
        org["name"] = process_placeholders(name, page, request)

    url = block_value.get("url", "")
    if url:
        org["url"] = process_placeholders(url, page, request)

    logo = block_value.get("logo")
    if logo:
        # Logo can be either a string URL or an ImageObjectBlock (dict)
        if isinstance(logo, dict):
            logo_data = _process_image_block(logo, page, request)
            if logo_data:
                org["logo"] = logo_data
        elif isinstance(logo, str) and logo:
            org["logo"] = process_placeholders(logo, page, request)

    return org if len(org) > 1 else None


def _process_image_block(block_value, page, request):
    """Process an ImageObject block into JSON-LD format."""
    image = {"@type": "ImageObject"}

    url = block_value.get("url", "")
    if url:
        image["url"] = process_placeholders(url, page, request)

    width = block_value.get("width")
    if width:
        image["width"] = width

    height = block_value.get("height")
    if height:
        image["height"] = height

    caption = block_value.get("caption", "")
    if caption:
        image["caption"] = process_placeholders(caption, page, request)

    return image if "url" in image else None


def _process_address_block(block_value, page, request):
    """Process a PostalAddress block into JSON-LD format."""
    address = {"@type": "PostalAddress"}

    if block_value.get("street_address"):
        address["streetAddress"] = block_value["street_address"]

    if block_value.get("address_locality"):
        address["addressLocality"] = block_value["address_locality"]

    if block_value.get("address_region"):
        address["addressRegion"] = block_value["address_region"]

    if block_value.get("postal_code"):
        address["postalCode"] = block_value["postal_code"]

    if block_value.get("address_country"):
        address["addressCountry"] = block_value["address_country"]

    return address if len(address) > 1 else None


def _process_contact_point_block(block_value, page, request):
    """Process a ContactPoint block into JSON-LD format."""
    contact = {"@type": "ContactPoint"}

    if block_value.get("telephone"):
        contact["telephone"] = block_value["telephone"]

    if block_value.get("email"):
        contact["email"] = block_value["email"]

    if block_value.get("contact_type"):
        contact["contactType"] = block_value["contact_type"]

    available_language = block_value.get("available_language", [])
    if available_language:
        contact["availableLanguage"] = list(available_language)

    return contact if len(contact) > 1 else None


def _process_speakable_block(block_value):
    """Process a SpeakableSpecification block into JSON-LD format."""
    speakable = {"@type": "SpeakableSpecification"}

    css_selector = block_value.get("css_selector", [])
    if css_selector:
        speakable["cssSelector"] = list(css_selector)

    xpath = block_value.get("xpath", [])
    if xpath:
        speakable["xpath"] = list(xpath)

    return speakable if len(speakable) > 1 else None


def _process_faq_item_block(block_value, page, request):
    """Process a FAQ item block into Question/Answer JSON-LD format."""
    question_text = block_value.get("question", "")
    answer_text = block_value.get("answer", "")

    if not question_text or not answer_text:
        return None

    return {
        "@type": "Question",
        "name": process_placeholders(question_text, page, request),
        "acceptedAnswer": {
            "@type": "Answer",
            "text": process_placeholders(answer_text, page, request),
        },
    }


def _process_monetary_amount_block(block_value, page, request):
    """Process a MonetaryAmount block into JSON-LD format."""
    amount = {"@type": "MonetaryAmount"}

    value = block_value.get("value", "")
    if value:
        amount["value"] = process_placeholders(value, page, request)

    currency = block_value.get("currency", "USD")
    if currency:
        amount["currency"] = currency

    return amount if "value" in amount else None


def _process_place_block(block_value, page, request):
    """Process a Place block into JSON-LD format."""
    place = {"@type": "Place"}

    name = block_value.get("name", "")
    if name:
        place["name"] = process_placeholders(name, page, request)

    # Process nested address
    address = block_value.get("address")
    if address:
        address_data = _process_address_block(address, page, request)
        if address_data:
            place["address"] = address_data

    # Process geo coordinates
    lat = block_value.get("geo_latitude")
    lng = block_value.get("geo_longitude")
    if lat and lng:
        place["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(lat),
            "longitude": float(lng),
        }

    return place if len(place) > 1 else None


# =============================================================================
# New Schema Block Processing Functions
# =============================================================================


def _process_offer_block(block_value, page, request):
    """Process an Offer block into JSON-LD format."""
    offer = {"@type": "Offer"}

    price = block_value.get("price", "")
    if price:
        offer["price"] = process_placeholders(price, page, request)

    currency = block_value.get("price_currency", "USD")
    if currency:
        offer["priceCurrency"] = currency

    availability = block_value.get("availability", "")
    if availability:
        offer["availability"] = f"https://schema.org/{availability}"

    url = block_value.get("url", "")
    if url:
        offer["url"] = process_placeholders(url, page, request)

    valid_from = block_value.get("valid_from", "")
    if valid_from:
        offer["validFrom"] = process_placeholders(valid_from, page, request)

    price_valid_until = block_value.get("price_valid_until", "")
    if price_valid_until:
        offer["priceValidUntil"] = process_placeholders(
            price_valid_until, page, request
        )

    item_condition = block_value.get("item_condition", "")
    if item_condition:
        offer["itemCondition"] = f"https://schema.org/{item_condition}"

    return offer if len(offer) > 1 else None


def _process_aggregate_offer_block(block_value, page, request):
    """Process an AggregateOffer block into JSON-LD format."""
    offer = {"@type": "AggregateOffer"}

    low_price = block_value.get("low_price", "")
    if low_price:
        offer["lowPrice"] = process_placeholders(low_price, page, request)

    high_price = block_value.get("high_price", "")
    if high_price:
        offer["highPrice"] = process_placeholders(high_price, page, request)

    offer_count = block_value.get("offer_count")
    if offer_count:
        offer["offerCount"] = offer_count

    currency = block_value.get("price_currency", "USD")
    if currency:
        offer["priceCurrency"] = currency

    return offer if len(offer) > 1 else None


def _process_aggregate_rating_block(block_value, page, request):
    """Process an AggregateRating block into JSON-LD format."""
    rating = {"@type": "AggregateRating"}

    rating_value = block_value.get("rating_value", "")
    if rating_value:
        rating["ratingValue"] = process_placeholders(rating_value, page, request)

    best_rating = block_value.get("best_rating", "5")
    if best_rating:
        rating["bestRating"] = best_rating

    worst_rating = block_value.get("worst_rating", "1")
    if worst_rating:
        rating["worstRating"] = worst_rating

    rating_count = block_value.get("rating_count", "")
    if rating_count:
        rating["ratingCount"] = process_placeholders(rating_count, page, request)

    review_count = block_value.get("review_count", "")
    if review_count:
        rating["reviewCount"] = process_placeholders(review_count, page, request)

    return rating if "ratingValue" in rating else None


def _process_review_item_block(block_value, page, request):
    """Process a ReviewItem block into JSON-LD format."""
    review = {"@type": "Review"}

    # Process author
    author = block_value.get("author")
    if author:
        author_data = _process_person_block(author, page, request)
        if author_data:
            review["author"] = author_data

    review_rating = block_value.get("review_rating", "")
    if review_rating:
        review["reviewRating"] = {
            "@type": "Rating",
            "ratingValue": process_placeholders(review_rating, page, request),
        }

    review_body = block_value.get("review_body", "")
    if review_body:
        review["reviewBody"] = process_placeholders(review_body, page, request)

    date_published = block_value.get("date_published", "")
    if date_published:
        review["datePublished"] = process_placeholders(date_published, page, request)

    return review if len(review) > 1 else None


def _process_howto_step_block(block_value, page, request):
    """Process a HowToStep block into JSON-LD format."""
    step = {"@type": "HowToStep"}

    name = block_value.get("name", "")
    if name:
        step["name"] = process_placeholders(name, page, request)

    text = block_value.get("text", "")
    if text:
        step["text"] = process_placeholders(text, page, request)

    # Process image
    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            step["image"] = image_data

    url = block_value.get("url", "")
    if url:
        step["url"] = process_placeholders(url, page, request)

    return step if "text" in step else None


def _process_howto_supply_block(block_value, page, request):
    """Process a HowToSupply block into JSON-LD format."""
    supply = {"@type": "HowToSupply"}

    name = block_value.get("name", "")
    if name:
        supply["name"] = process_placeholders(name, page, request)

    image = block_value.get("image", "")
    if image:
        supply["image"] = process_placeholders(image, page, request)

    return supply if "name" in supply else None


def _process_howto_tool_block(block_value, page, request):
    """Process a HowToTool block into JSON-LD format."""
    tool = {"@type": "HowToTool"}

    name = block_value.get("name", "")
    if name:
        tool["name"] = process_placeholders(name, page, request)

    image = block_value.get("image", "")
    if image:
        tool["image"] = process_placeholders(image, page, request)

    return tool if "name" in tool else None


def _process_breadcrumb_item_block(block_value, page, request):
    """Process a BreadcrumbItem block into JSON-LD ListItem format."""
    item = {"@type": "ListItem"}

    name = block_value.get("name", "")
    if name:
        item["name"] = process_placeholders(name, page, request)

    url = block_value.get("url", "")
    if url:
        item["item"] = process_placeholders(url, page, request)

    return item if "name" in item and "item" in item else None


def _process_item_list_element_block(block_value, page, request):
    """Process an ItemListElement block into JSON-LD format."""
    item = {"@type": "ListItem"}

    name = block_value.get("name", "")
    if name:
        item["name"] = process_placeholders(name, page, request)

    url = block_value.get("url", "")
    if url:
        item["url"] = process_placeholders(url, page, request)

    image = block_value.get("image", "")
    if image:
        item["image"] = process_placeholders(image, page, request)

    return item if "url" in item else None


def _process_menu_item_block(block_value, page, request):
    """Process a MenuItem block into JSON-LD format."""
    item = {"@type": "MenuItem"}

    name = block_value.get("name", "")
    if name:
        item["name"] = process_placeholders(name, page, request)

    description = block_value.get("description", "")
    if description:
        item["description"] = process_placeholders(description, page, request)

    price = block_value.get("price", "")
    currency = block_value.get("price_currency", "USD")
    if price:
        item["offers"] = {
            "@type": "Offer",
            "price": process_placeholders(price, page, request),
            "priceCurrency": currency,
        }

    image = block_value.get("image", "")
    if image:
        item["image"] = process_placeholders(image, page, request)

    return item if "name" in item else None


def _process_menu_section_block(block_value, page, request):
    """Process a MenuSection block into JSON-LD format."""
    section = {"@type": "MenuSection"}

    name = block_value.get("name", "")
    if name:
        section["name"] = process_placeholders(name, page, request)

    description = block_value.get("description", "")
    if description:
        section["description"] = process_placeholders(description, page, request)

    # Process menu items
    menu_items = block_value.get("has_menu_item", [])
    if menu_items:
        section["hasMenuItem"] = []
        for item in menu_items:
            item_data = _process_menu_item_block(item, page, request)
            if item_data:
                section["hasMenuItem"].append(item_data)

    return section if "name" in section else None


# =============================================================================
# Main Schema Block Converters
# =============================================================================


def schema_block_to_jsonld(block_type, block_value, page, request=None):
    """
    Convert a main schema block to complete JSON-LD structure.

    Args:
        block_type: The type of schema block (e.g., 'article', 'product')
        block_value: The block's value dict
        page: Wagtail Page instance
        request: Optional request for URL generation

    Returns:
        Complete JSON-LD dict with @context and @type
    """
    converters = {
        "article": _convert_article_schema,
        "blog_posting": _convert_blog_posting_schema,
        "news_article": _convert_news_article_schema,
        "web_page": _convert_web_page_schema,
        "faq_page": _convert_faq_page_schema,
        "product": _convert_product_schema,
        "service": _convert_service_schema,
        "software_app": _convert_software_application_schema,
        "job_posting": _convert_job_posting_schema,
        "how_to": _convert_howto_schema,
        "recipe": _convert_recipe_schema,
        "video": _convert_video_object_schema,
        "audio": _convert_audio_object_schema,
        "podcast_series": _convert_podcast_series_schema,
        "podcast_episode": _convert_podcast_episode_schema,
        "review": _convert_review_schema,
        "organization": _convert_organization_schema,
        "person": _convert_person_schema,
        "profile_page": _convert_profile_page_schema,
        "event": _convert_event_schema,
        "project": _convert_project_schema,
        "restaurant": _convert_restaurant_schema,
        "menu": _convert_menu_schema,
        "breadcrumb_list": _convert_breadcrumb_list_schema,
        "item_list": _convert_item_list_schema,
        "report": _convert_report_schema,
        "scholarly_article": _convert_scholarly_article_schema,
        "place": _convert_place_schema,
        "monetary_grant": _convert_monetary_grant_schema,
        "book": _convert_book_schema,
        "custom_schema": _convert_custom_schema,
    }

    converter = converters.get(block_type)
    if converter:
        return converter(block_value, page, request)

    return None


def _convert_article_schema(block_value, page, request):
    """Convert Article schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
    }

    if block_value.get("headline"):
        schema["headline"] = process_placeholders(
            block_value["headline"], page, request
        )

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    if block_value.get("date_modified"):
        schema["dateModified"] = process_placeholders(
            block_value["date_modified"], page, request
        )

    author = block_value.get("author")
    if author:
        author_data = _process_person_block(author, page, request)
        if author_data:
            schema["author"] = author_data

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    speakable = block_value.get("speakable")
    if speakable:
        speakable_data = _process_speakable_block(speakable)
        if speakable_data:
            schema["speakable"] = speakable_data

    # Process additional properties
    additional = block_value.get("additional_properties", [])
    for prop in additional:
        prop_name = prop.get("property_name", "")
        prop_value = prop.get("value", "")
        if prop_name and prop_value:
            schema[prop_name] = process_placeholders(prop_value, page, request)

    return schema


def _convert_blog_posting_schema(block_value, page, request):
    """Convert BlogPosting schema block to JSON-LD."""
    schema = _convert_article_schema(block_value, page, request)
    schema["@type"] = "BlogPosting"

    if block_value.get("word_count"):
        schema["wordCount"] = process_placeholders(
            block_value["word_count"], page, request
        )

    return schema


def _convert_news_article_schema(block_value, page, request):
    """Convert NewsArticle schema block to JSON-LD."""
    schema = _convert_article_schema(block_value, page, request)
    schema["@type"] = "NewsArticle"

    if block_value.get("dateline"):
        schema["dateline"] = process_placeholders(
            block_value["dateline"], page, request
        )

    return schema


def _convert_web_page_schema(block_value, page, request):
    """Convert WebPage schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    if block_value.get("date_modified"):
        schema["dateModified"] = process_placeholders(
            block_value["date_modified"], page, request
        )

    speakable = block_value.get("speakable")
    if speakable:
        speakable_data = _process_speakable_block(speakable)
        if speakable_data:
            schema["speakable"] = speakable_data

    # Process additional properties
    additional = block_value.get("additional_properties", [])
    for prop in additional:
        prop_name = prop.get("property_name", "")
        prop_value = prop.get("value", "")
        if prop_name and prop_value:
            schema[prop_name] = process_placeholders(prop_value, page, request)

    return schema


def _convert_faq_page_schema(block_value, page, request):
    """Convert FAQPage schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [],
    }

    main_entity = block_value.get("main_entity", [])
    for faq_item in main_entity:
        faq_data = _process_faq_item_block(faq_item, page, request)
        if faq_data:
            schema["mainEntity"].append(faq_data)

    return schema


def _convert_product_schema(block_value, page, request):
    """Convert Product schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    if block_value.get("brand"):
        schema["brand"] = {
            "@type": "Brand",
            "name": process_placeholders(block_value["brand"], page, request),
        }

    if block_value.get("sku"):
        schema["sku"] = block_value["sku"]

    if block_value.get("gtin"):
        schema["gtin"] = block_value["gtin"]

    if block_value.get("mpn"):
        schema["mpn"] = block_value["mpn"]

    if block_value.get("category"):
        schema["category"] = process_placeholders(
            block_value["category"], page, request
        )

    if block_value.get("color"):
        schema["color"] = process_placeholders(block_value["color"], page, request)

    if block_value.get("material"):
        schema["material"] = process_placeholders(
            block_value["material"], page, request
        )

    # Process offers
    offers = block_value.get("offers")
    if offers:
        offer_data = _process_offer_block(offers, page, request)
        if offer_data:
            schema["offers"] = offer_data

    aggregate_offer = block_value.get("aggregate_offer")
    if aggregate_offer:
        agg_offer_data = _process_aggregate_offer_block(aggregate_offer, page, request)
        if agg_offer_data:
            schema["offers"] = agg_offer_data

    # Process rating
    aggregate_rating = block_value.get("aggregate_rating")
    if aggregate_rating:
        rating_data = _process_aggregate_rating_block(aggregate_rating, page, request)
        if rating_data:
            schema["aggregateRating"] = rating_data

    # Process reviews
    reviews = block_value.get("review", [])
    if reviews:
        schema["review"] = []
        for review in reviews:
            review_data = _process_review_item_block(review, page, request)
            if review_data:
                schema["review"].append(review_data)

    return schema


def _convert_service_schema(block_value, page, request):
    """Convert Service schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Service",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("service_type"):
        schema["serviceType"] = process_placeholders(
            block_value["service_type"], page, request
        )

    provider = block_value.get("provider")
    if provider:
        provider_data = _process_organization_block(provider, page, request)
        if provider_data:
            schema["provider"] = provider_data

    if block_value.get("area_served"):
        schema["areaServed"] = process_placeholders(
            block_value["area_served"], page, request
        )

    offers = block_value.get("offers")
    if offers:
        offer_data = _process_offer_block(offers, page, request)
        if offer_data:
            schema["offers"] = offer_data

    aggregate_rating = block_value.get("aggregate_rating")
    if aggregate_rating:
        rating_data = _process_aggregate_rating_block(aggregate_rating, page, request)
        if rating_data:
            schema["aggregateRating"] = rating_data

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    return schema


def _convert_software_application_schema(block_value, page, request):
    """Convert SoftwareApplication schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("application_category"):
        schema["applicationCategory"] = block_value["application_category"]

    if block_value.get("operating_system"):
        schema["operatingSystem"] = block_value["operating_system"]

    if block_value.get("software_version"):
        schema["softwareVersion"] = block_value["software_version"]

    offers = block_value.get("offers")
    if offers:
        offer_data = _process_offer_block(offers, page, request)
        if offer_data:
            schema["offers"] = offer_data

    aggregate_rating = block_value.get("aggregate_rating")
    if aggregate_rating:
        rating_data = _process_aggregate_rating_block(aggregate_rating, page, request)
        if rating_data:
            schema["aggregateRating"] = rating_data

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    if block_value.get("download_url"):
        schema["downloadUrl"] = process_placeholders(
            block_value["download_url"], page, request
        )

    return schema


def _convert_job_posting_schema(block_value, page, request):
    """Convert JobPosting schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
    }

    if block_value.get("title"):
        schema["title"] = process_placeholders(block_value["title"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("date_posted"):
        schema["datePosted"] = process_placeholders(
            block_value["date_posted"], page, request
        )

    if block_value.get("valid_through"):
        schema["validThrough"] = process_placeholders(
            block_value["valid_through"], page, request
        )

    if block_value.get("employment_type"):
        schema["employmentType"] = block_value["employment_type"]

    hiring_org = block_value.get("hiring_organization")
    if hiring_org:
        org_data = _process_organization_block(hiring_org, page, request)
        if org_data:
            schema["hiringOrganization"] = org_data

    job_location = block_value.get("job_location")
    if job_location:
        place_data = _process_place_block(job_location, page, request)
        if place_data:
            schema["jobLocation"] = place_data

    if block_value.get("job_location_type") == "TELECOMMUTE":
        schema["jobLocationType"] = "TELECOMMUTE"

    base_salary = block_value.get("base_salary")
    if base_salary:
        salary_data = _process_monetary_amount_block(base_salary, page, request)
        if salary_data:
            schema["baseSalary"] = salary_data
            if block_value.get("salary_unit"):
                schema["baseSalary"]["unitText"] = block_value["salary_unit"]

    if block_value.get("qualifications"):
        schema["qualifications"] = process_placeholders(
            block_value["qualifications"], page, request
        )

    if block_value.get("responsibilities"):
        schema["responsibilities"] = process_placeholders(
            block_value["responsibilities"], page, request
        )

    if block_value.get("benefits"):
        schema["jobBenefits"] = process_placeholders(
            block_value["benefits"], page, request
        )

    return schema


def _convert_howto_schema(block_value, page, request):
    """Convert HowTo schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    if block_value.get("total_time"):
        schema["totalTime"] = block_value["total_time"]

    estimated_cost = block_value.get("estimated_cost")
    if estimated_cost:
        cost_data = _process_monetary_amount_block(estimated_cost, page, request)
        if cost_data:
            schema["estimatedCost"] = cost_data

    # Process supplies
    supplies = block_value.get("supply", [])
    if supplies:
        schema["supply"] = []
        for supply in supplies:
            supply_data = _process_howto_supply_block(supply, page, request)
            if supply_data:
                schema["supply"].append(supply_data)

    # Process tools
    tools = block_value.get("tool", [])
    if tools:
        schema["tool"] = []
        for tool in tools:
            tool_data = _process_howto_tool_block(tool, page, request)
            if tool_data:
                schema["tool"].append(tool_data)

    # Process steps
    steps = block_value.get("step", [])
    if steps:
        schema["step"] = []
        for step in steps:
            step_data = _process_howto_step_block(step, page, request)
            if step_data:
                schema["step"].append(step_data)

    return schema


def _convert_recipe_schema(block_value, page, request):
    """Convert Recipe schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    author = block_value.get("author")
    if author:
        author_data = _process_person_block(author, page, request)
        if author_data:
            schema["author"] = author_data

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    if block_value.get("prep_time"):
        schema["prepTime"] = block_value["prep_time"]

    if block_value.get("cook_time"):
        schema["cookTime"] = block_value["cook_time"]

    if block_value.get("total_time"):
        schema["totalTime"] = block_value["total_time"]

    if block_value.get("recipe_yield"):
        schema["recipeYield"] = block_value["recipe_yield"]

    if block_value.get("recipe_category"):
        schema["recipeCategory"] = block_value["recipe_category"]

    if block_value.get("recipe_cuisine"):
        schema["recipeCuisine"] = block_value["recipe_cuisine"]

    # Process ingredients
    ingredients = block_value.get("recipe_ingredient", [])
    if ingredients:
        schema["recipeIngredient"] = list(ingredients)

    # Process instructions
    instructions = block_value.get("recipe_instructions", [])
    if instructions:
        schema["recipeInstructions"] = []
        for instruction in instructions:
            text = instruction.get("text", "")
            if text:
                schema["recipeInstructions"].append(
                    {
                        "@type": "HowToStep",
                        "text": process_placeholders(text, page, request),
                    }
                )

    # Process nutrition
    nutrition = block_value.get("nutrition")
    if nutrition:
        nutrition_data = {"@type": "NutritionInformation"}
        if nutrition.get("calories"):
            nutrition_data["calories"] = nutrition["calories"]
        if nutrition.get("fat_content"):
            nutrition_data["fatContent"] = nutrition["fat_content"]
        if nutrition.get("carbohydrate_content"):
            nutrition_data["carbohydrateContent"] = nutrition["carbohydrate_content"]
        if nutrition.get("protein_content"):
            nutrition_data["proteinContent"] = nutrition["protein_content"]
        if len(nutrition_data) > 1:
            schema["nutrition"] = nutrition_data

    return schema


def _convert_video_object_schema(block_value, page, request):
    """Convert VideoObject schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("thumbnail_url"):
        schema["thumbnailUrl"] = process_placeholders(
            block_value["thumbnail_url"], page, request
        )

    if block_value.get("upload_date"):
        schema["uploadDate"] = process_placeholders(
            block_value["upload_date"], page, request
        )

    if block_value.get("duration"):
        schema["duration"] = block_value["duration"]

    if block_value.get("content_url"):
        schema["contentUrl"] = process_placeholders(
            block_value["content_url"], page, request
        )

    if block_value.get("embed_url"):
        schema["embedUrl"] = process_placeholders(
            block_value["embed_url"], page, request
        )

    if block_value.get("transcript"):
        schema["transcript"] = process_placeholders(
            block_value["transcript"], page, request
        )

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    return schema


def _convert_audio_object_schema(block_value, page, request):
    """Convert AudioObject schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "AudioObject",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("content_url"):
        schema["contentUrl"] = process_placeholders(
            block_value["content_url"], page, request
        )

    if block_value.get("duration"):
        schema["duration"] = block_value["duration"]

    if block_value.get("encoding_format"):
        schema["encodingFormat"] = block_value["encoding_format"]

    if block_value.get("transcript"):
        schema["transcript"] = process_placeholders(
            block_value["transcript"], page, request
        )

    if block_value.get("upload_date"):
        schema["uploadDate"] = process_placeholders(
            block_value["upload_date"], page, request
        )

    return schema


def _convert_podcast_series_schema(block_value, page, request):
    """Convert PodcastSeries schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "PodcastSeries",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    author = block_value.get("author")
    if author:
        author_data = _process_person_block(author, page, request)
        if author_data:
            schema["author"] = author_data

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    if block_value.get("url"):
        schema["url"] = process_placeholders(block_value["url"], page, request)

    if block_value.get("web_feed"):
        schema["webFeed"] = process_placeholders(block_value["web_feed"], page, request)

    return schema


def _convert_podcast_episode_schema(block_value, page, request):
    """Convert PodcastEpisode schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "PodcastEpisode",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    if block_value.get("duration"):
        schema["duration"] = block_value["duration"]

    if block_value.get("episode_number"):
        schema["episodeNumber"] = block_value["episode_number"]

    if block_value.get("season_number"):
        schema["partOfSeason"] = {
            "@type": "PodcastSeason",
            "seasonNumber": block_value["season_number"],
        }

    if block_value.get("audio"):
        schema["audio"] = {
            "@type": "AudioObject",
            "contentUrl": process_placeholders(block_value["audio"], page, request),
        }

    if block_value.get("part_of_series"):
        schema["partOfSeries"] = {
            "@type": "PodcastSeries",
            "name": process_placeholders(block_value["part_of_series"], page, request),
        }

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    return schema


def _convert_review_schema(block_value, page, request):
    """Convert Review schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Review",
    }

    # Item reviewed
    item_type = block_value.get("item_reviewed_type", "Thing")
    item_name = block_value.get("item_reviewed_name", "")
    if item_name:
        schema["itemReviewed"] = {
            "@type": item_type or "Thing",
            "name": process_placeholders(item_name, page, request),
        }
        if block_value.get("item_reviewed_url"):
            schema["itemReviewed"]["url"] = process_placeholders(
                block_value["item_reviewed_url"], page, request
            )

    author = block_value.get("author")
    if author:
        author_data = _process_person_block(author, page, request)
        if author_data:
            schema["author"] = author_data

    if block_value.get("review_rating"):
        schema["reviewRating"] = {
            "@type": "Rating",
            "ratingValue": process_placeholders(
                block_value["review_rating"], page, request
            ),
            "bestRating": block_value.get("best_rating", "5"),
            "worstRating": block_value.get("worst_rating", "1"),
        }

    if block_value.get("review_body"):
        schema["reviewBody"] = process_placeholders(
            block_value["review_body"], page, request
        )

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    return schema


def _convert_organization_schema(block_value, page, request):
    """Convert Organization schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("url"):
        schema["url"] = process_placeholders(block_value["url"], page, request)

    if block_value.get("logo"):
        schema["logo"] = process_placeholders(block_value["logo"], page, request)

    address = block_value.get("address")
    if address:
        address_data = _process_address_block(address, page, request)
        if address_data:
            schema["address"] = address_data

    contact_points = block_value.get("contact_point", [])
    if contact_points:
        schema["contactPoint"] = []
        for contact in contact_points:
            contact_data = _process_contact_point_block(contact, page, request)
            if contact_data:
                schema["contactPoint"].append(contact_data)

    same_as = block_value.get("same_as", [])
    if same_as:
        schema["sameAs"] = list(same_as)

    return schema


def _convert_person_schema(block_value, page, request):
    """Convert Person schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("job_title"):
        schema["jobTitle"] = process_placeholders(
            block_value["job_title"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    works_for = block_value.get("works_for")
    if works_for:
        org_data = _process_organization_block(works_for, page, request)
        if org_data:
            schema["worksFor"] = org_data

    same_as = block_value.get("same_as", [])
    if same_as:
        schema["sameAs"] = list(same_as)

    return schema


def _convert_profile_page_schema(block_value, page, request):
    """Convert ProfilePage schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
    }

    if block_value.get("date_created"):
        schema["dateCreated"] = process_placeholders(
            block_value["date_created"], page, request
        )

    if block_value.get("date_modified"):
        schema["dateModified"] = process_placeholders(
            block_value["date_modified"], page, request
        )

    # Main entity (the person)
    main_entity = {"@type": "Person"}

    if block_value.get("main_entity_name"):
        main_entity["name"] = process_placeholders(
            block_value["main_entity_name"], page, request
        )

    if block_value.get("main_entity_job_title"):
        main_entity["jobTitle"] = process_placeholders(
            block_value["main_entity_job_title"], page, request
        )

    if block_value.get("main_entity_description"):
        main_entity["description"] = process_placeholders(
            block_value["main_entity_description"], page, request
        )

    if block_value.get("main_entity_image"):
        main_entity["image"] = process_placeholders(
            block_value["main_entity_image"], page, request
        )

    if block_value.get("main_entity_url"):
        main_entity["url"] = process_placeholders(
            block_value["main_entity_url"], page, request
        )

    works_for = block_value.get("works_for")
    if works_for:
        org_data = _process_organization_block(works_for, page, request)
        if org_data:
            main_entity["worksFor"] = org_data

    same_as = block_value.get("same_as", [])
    if same_as:
        main_entity["sameAs"] = list(same_as)

    if len(main_entity) > 1:
        schema["mainEntity"] = main_entity

    return schema


def _convert_event_schema(block_value, page, request):
    """Convert Event schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("start_date"):
        schema["startDate"] = process_placeholders(
            block_value["start_date"], page, request
        )

    if block_value.get("end_date"):
        schema["endDate"] = process_placeholders(block_value["end_date"], page, request)

    location = block_value.get("location")
    if location:
        place_data = _process_place_block(location, page, request)
        if place_data:
            schema["location"] = place_data

    organizer = block_value.get("organizer")
    if organizer:
        org_data = _process_organization_block(organizer, page, request)
        if org_data:
            schema["organizer"] = org_data

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    return schema


def _convert_project_schema(block_value, page, request):
    """Convert Project schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Project",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("start_date"):
        schema["startDate"] = process_placeholders(
            block_value["start_date"], page, request
        )

    if block_value.get("end_date"):
        schema["endDate"] = process_placeholders(block_value["end_date"], page, request)

    funder = block_value.get("funder")
    if funder:
        funder_data = _process_organization_block(funder, page, request)
        if funder_data:
            schema["funder"] = funder_data

    location = block_value.get("location")
    if location:
        place_data = _process_place_block(location, page, request)
        if place_data:
            schema["location"] = place_data

    return schema


def _convert_restaurant_schema(block_value, page, request):
    """Convert Restaurant schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Restaurant",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    address = block_value.get("address")
    if address:
        address_data = _process_address_block(address, page, request)
        if address_data:
            schema["address"] = address_data

    if block_value.get("telephone"):
        schema["telephone"] = block_value["telephone"]

    if block_value.get("url"):
        schema["url"] = process_placeholders(block_value["url"], page, request)

    if block_value.get("serves_cuisine"):
        schema["servesCuisine"] = block_value["serves_cuisine"]

    if block_value.get("price_range"):
        schema["priceRange"] = block_value["price_range"]

    opening_hours = block_value.get("opening_hours", [])
    if opening_hours:
        schema["openingHours"] = list(opening_hours)

    if block_value.get("accepts_reservations"):
        schema["acceptsReservations"] = True

    if block_value.get("menu_url"):
        schema["hasMenu"] = process_placeholders(block_value["menu_url"], page, request)

    # Geo coordinates
    lat = block_value.get("geo_latitude")
    lng = block_value.get("geo_longitude")
    if lat and lng:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(lat),
            "longitude": float(lng),
        }

    aggregate_rating = block_value.get("aggregate_rating")
    if aggregate_rating:
        rating_data = _process_aggregate_rating_block(aggregate_rating, page, request)
        if rating_data:
            schema["aggregateRating"] = rating_data

    same_as = block_value.get("same_as", [])
    if same_as:
        schema["sameAs"] = list(same_as)

    return schema


def _convert_menu_schema(block_value, page, request):
    """Convert Menu schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Menu",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    # Process menu sections
    sections = block_value.get("has_menu_section", [])
    if sections:
        schema["hasMenuSection"] = []
        for section in sections:
            section_data = _process_menu_section_block(section, page, request)
            if section_data:
                schema["hasMenuSection"].append(section_data)

    return schema


def _convert_breadcrumb_list_schema(block_value, page, request):
    """Convert BreadcrumbList schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [],
    }

    items = block_value.get("items", [])
    for position, item in enumerate(items, start=1):
        item_data = _process_breadcrumb_item_block(item, page, request)
        if item_data:
            item_data["position"] = position
            schema["itemListElement"].append(item_data)

    return schema


def _convert_item_list_schema(block_value, page, request):
    """Convert ItemList schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("item_list_order"):
        schema["itemListOrder"] = f"https://schema.org/{block_value['item_list_order']}"

    items = block_value.get("item_list_element", [])
    if items:
        schema["itemListElement"] = []
        for position, item in enumerate(items, start=1):
            item_data = _process_item_list_element_block(item, page, request)
            if item_data:
                item_data["position"] = position
                schema["itemListElement"].append(item_data)

    return schema


def _convert_report_schema(block_value, page, request):
    """Convert Report schema block to JSON-LD."""
    schema = _convert_article_schema(block_value, page, request)
    schema["@type"] = "Report"

    encoding = block_value.get("encoding")
    if encoding:
        encoding_data = {"@type": "MediaObject"}
        if encoding.get("content_url"):
            encoding_data["contentUrl"] = process_placeholders(
                encoding["content_url"], page, request
            )
        if encoding.get("encoding_format"):
            encoding_data["encodingFormat"] = encoding["encoding_format"]
        if encoding.get("name"):
            encoding_data["name"] = process_placeholders(
                encoding["name"], page, request
            )
        if len(encoding_data) > 1:
            schema["encoding"] = encoding_data

    return schema


def _convert_scholarly_article_schema(block_value, page, request):
    """Convert ScholarlyArticle schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
    }

    if block_value.get("headline"):
        schema["headline"] = process_placeholders(
            block_value["headline"], page, request
        )

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    # Multiple authors
    authors = block_value.get("author", [])
    if authors:
        schema["author"] = []
        for author in authors:
            author_data = _process_person_block(author, page, request)
            if author_data:
                schema["author"].append(author_data)

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    encoding = block_value.get("encoding")
    if encoding:
        encoding_data = {"@type": "MediaObject"}
        if encoding.get("content_url"):
            encoding_data["contentUrl"] = process_placeholders(
                encoding["content_url"], page, request
            )
        if encoding.get("encoding_format"):
            encoding_data["encodingFormat"] = encoding["encoding_format"]
        if len(encoding_data) > 1:
            schema["encoding"] = encoding_data

    return schema


def _convert_place_schema(block_value, page, request):
    """Convert Place schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Place",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    address = block_value.get("address")
    if address:
        address_data = _process_address_block(address, page, request)
        if address_data:
            schema["address"] = address_data

    lat = block_value.get("geo_latitude")
    lng = block_value.get("geo_longitude")
    if lat and lng:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(lat),
            "longitude": float(lng),
        }

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    return schema


def _convert_monetary_grant_schema(block_value, page, request):
    """Convert MonetaryGrant schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MonetaryGrant",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    amount = block_value.get("amount")
    if amount:
        amount_data = _process_monetary_amount_block(amount, page, request)
        if amount_data:
            schema["amount"] = amount_data

    funder = block_value.get("funder")
    if funder:
        funder_data = _process_organization_block(funder, page, request)
        if funder_data:
            schema["funder"] = funder_data

    if block_value.get("funded_item"):
        schema["fundedItem"] = process_placeholders(
            block_value["funded_item"], page, request
        )

    return schema


def _convert_book_schema(block_value, page, request):
    """Convert Book schema block to JSON-LD."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Book",
    }

    if block_value.get("name"):
        schema["name"] = process_placeholders(block_value["name"], page, request)

    if block_value.get("description"):
        schema["description"] = process_placeholders(
            block_value["description"], page, request
        )

    # Multiple authors
    authors = block_value.get("author", [])
    if authors:
        schema["author"] = []
        for author in authors:
            author_data = _process_person_block(author, page, request)
            if author_data:
                schema["author"].append(author_data)

    if block_value.get("isbn"):
        schema["isbn"] = block_value["isbn"]

    if block_value.get("book_edition"):
        schema["bookEdition"] = block_value["book_edition"]

    if block_value.get("book_format"):
        schema["bookFormat"] = f"https://schema.org/{block_value['book_format']}"

    if block_value.get("number_of_pages"):
        schema["numberOfPages"] = block_value["number_of_pages"]

    publisher = block_value.get("publisher")
    if publisher:
        publisher_data = _process_organization_block(publisher, page, request)
        if publisher_data:
            schema["publisher"] = publisher_data

    if block_value.get("date_published"):
        schema["datePublished"] = process_placeholders(
            block_value["date_published"], page, request
        )

    if block_value.get("in_language"):
        schema["inLanguage"] = block_value["in_language"]

    image = block_value.get("image")
    if image:
        image_data = _process_image_block(image, page, request)
        if image_data:
            schema["image"] = image_data

    aggregate_rating = block_value.get("aggregate_rating")
    if aggregate_rating:
        rating_data = _process_aggregate_rating_block(aggregate_rating, page, request)
        if rating_data:
            schema["aggregateRating"] = rating_data

    return schema


def _convert_custom_schema(block_value, page, request):
    """
    Convert Custom schema block to JSON-LD.
    Allows users to build any schema.org type from scratch with complete flexibility.
    """
    schema_type = block_value.get("schema_type", "Thing")

    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
    }

    # Process all properties (key-value pairs)
    properties = block_value.get("properties", [])
    for prop in properties:
        prop_name = prop.get("property_name", "")
        prop_value = prop.get("value", "")
        if prop_name and prop_value:
            schema[prop_name] = process_placeholders(prop_value, page, request)

    # Process nested objects (complex structures with their own @type)
    nested_objects = block_value.get("nested_objects", [])
    for nested in nested_objects:
        prop_key = nested.get("property_name", "")
        object_type = nested.get("object_type", "")
        nested_properties = nested.get("properties", [])

        if prop_key and object_type:
            nested_obj = {"@type": object_type}

            for prop in nested_properties:
                prop_name = prop.get("property_name", "")
                prop_value = prop.get("value", "")
                if prop_name and prop_value:
                    nested_obj[prop_name] = process_placeholders(
                        prop_value, page, request
                    )

            if len(nested_obj) > 1:
                # If this property already exists, convert to list
                if prop_key in schema:
                    if isinstance(schema[prop_key], list):
                        schema[prop_key].append(nested_obj)
                    else:
                        schema[prop_key] = [schema[prop_key], nested_obj]
                else:
                    schema[prop_key] = nested_obj

    return schema


def generate_breadcrumb_jsonld(page, request=None):
    """
    Generate BreadcrumbList JSON-LD from page hierarchy.

    Auto-generates breadcrumbs from the page's ancestors.
    Can be disabled via WAGTAIL_SEOTOOLKIT_JSONLD_AUTO_BREADCRUMBS setting.

    Args:
        page: Wagtail Page instance
        request: Optional request for URL generation

    Returns:
        BreadcrumbList JSON-LD dict, or None if disabled
    """
    if not getattr(settings, "WAGTAIL_SEOTOOLKIT_JSONLD_AUTO_BREADCRUMBS", True):
        return None

    ancestors = page.get_ancestors().live().exclude(depth__lt=2)

    if not ancestors:
        return None

    items = []
    position = 1

    for ancestor in ancestors:
        item = {
            "@type": "ListItem",
            "position": position,
            "name": ancestor.title,
        }

        if request:
            item["item"] = request.build_absolute_uri(ancestor.url)
        else:
            item["item"] = ancestor.url

        items.append(item)
        position += 1

    # Add current page
    current_item = {
        "@type": "ListItem",
        "position": position,
        "name": page.title,
    }
    if request:
        current_item["item"] = request.build_absolute_uri(page.url)
    else:
        current_item["item"] = page.url
    items.append(current_item)

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def generate_language_jsonld(page, request=None):
    """
    Generate language/translation JSON-LD from Wagtail locales.

    Auto-generates inLanguage and translation links from page translations.
    Can be disabled via WAGTAIL_SEOTOOLKIT_JSONLD_AUTO_LANGUAGE setting.

    Args:
        page: Wagtail Page instance
        request: Optional request for URL generation

    Returns:
        Dict with inLanguage and potentialAction for translations, or None
    """
    if not getattr(settings, "WAGTAIL_SEOTOOLKIT_JSONLD_AUTO_LANGUAGE", True):
        return None

    # Check if page has locale support
    if not hasattr(page, "locale"):
        return None

    result = {}

    # Add current page language
    if page.locale:
        result["inLanguage"] = page.locale.language_code

    # Get translations if available
    if hasattr(page, "get_translations"):
        translations = page.get_translations().live()
        if translations.exists():
            result["workTranslation"] = []
            for translation in translations:
                trans_data = {
                    "@type": "WebPage",
                    "inLanguage": translation.locale.language_code,
                }
                if request:
                    trans_data["url"] = request.build_absolute_uri(translation.url)
                else:
                    trans_data["url"] = translation.url
                result["workTranslation"].append(trans_data)

    return result if result else None


def _merge_schemas_by_type(base_schemas, override_schemas):
    """
    Merge two lists of schemas. Override schemas take precedence for same @type.

    For schemas with the same @type, the override values are merged on top of base values.
    Schemas with unique @types are kept as-is.

    Args:
        base_schemas: List of base schema dicts (lower priority)
        override_schemas: List of override schema dicts (higher priority)

    Returns:
        List of merged schema dicts
    """
    result = {}

    # Add base schemas first
    for schema in base_schemas:
        schema_type = schema.get("@type", "Unknown")
        result[schema_type] = schema.copy()

    # Override with more specific schemas
    for schema in override_schemas:
        schema_type = schema.get("@type", "Unknown")
        if schema_type in result:
            # Merge: override values take precedence
            result[schema_type].update(schema)
        else:
            result[schema_type] = schema.copy()

    return list(result.values())


def _convert_streamfield_schemas(schemas_streamfield, page, request):
    """
    Convert a schemas StreamField to list of JSON-LD dicts.

    Args:
        schemas_streamfield: StreamField value containing schema blocks
        page: Wagtail Page instance
        request: Optional request for URL generation

    Returns:
        List of JSON-LD schema dicts
    """
    schemas = []

    if not schemas_streamfield:
        return schemas

    for block in schemas_streamfield:
        block_type = block.block_type
        block_value = block.value

        # Convert the block to JSON-LD
        schema = schema_block_to_jsonld(block_type, block_value, page, request)
        if schema:
            schemas.append(schema)

    return schemas


def _convert_site_wide_schemas(schemas_streamfield, site, page, request):
    """
    Convert site-wide schemas StreamField to list of JSON-LD dicts.

    Site-wide schemas (Organization, WebSite, LocalBusiness) have their
    name and URL auto-populated from Wagtail Site settings.

    Args:
        schemas_streamfield: StreamField value containing site-wide schema blocks
        site: Wagtail Site instance
        page: Wagtail Page instance
        request: Optional request for URL generation

    Returns:
        List of JSON-LD schema dicts
    """
    schemas = []

    if not schemas_streamfield:
        return schemas

    # Get site info for auto-population
    site_name = site.site_name if site else ""
    site_url = site.root_url if site else ""

    for block in schemas_streamfield:
        block_type = block.block_type
        block_value = block.value

        schema = {"@context": "https://schema.org"}

        if block_type == "organization":
            schema["@type"] = "Organization"
            schema["name"] = site_name
            schema["url"] = site_url

            if block_value.get("description"):
                schema["description"] = block_value["description"]
            if block_value.get("logo"):
                schema["logo"] = block_value["logo"]

            # Process address
            address = block_value.get("address")
            if address:
                address_data = _process_address_block(address, page, request)
                if address_data:
                    schema["address"] = address_data

            # Process contact points
            contact_points = block_value.get("contact_point", [])
            if contact_points:
                schema["contactPoint"] = []
                for contact in contact_points:
                    contact_data = _process_contact_point_block(contact, page, request)
                    if contact_data:
                        schema["contactPoint"].append(contact_data)

            # Social media URLs
            same_as = block_value.get("same_as", [])
            if same_as:
                schema["sameAs"] = list(same_as)

            if block_value.get("founding_date"):
                schema["foundingDate"] = block_value["founding_date"]

        elif block_type == "website":
            schema["@type"] = "WebSite"
            schema["name"] = site_name
            schema["url"] = site_url

            if block_value.get("description"):
                schema["description"] = block_value["description"]

            # Publisher
            publisher = block_value.get("publisher")
            if publisher:
                publisher_data = _process_organization_block(publisher, page, request)
                if publisher_data:
                    schema["publisher"] = publisher_data

            # Search action
            if block_value.get("potential_action_search"):
                search_template = block_value.get(
                    "search_url_template", "/search/?q={search_term_string}"
                )
                schema["potentialAction"] = {
                    "@type": "SearchAction",
                    "target": f"{site_url}{search_template}",
                    "query-input": "required name=search_term_string",
                }

            if block_value.get("in_language"):
                schema["inLanguage"] = block_value["in_language"]

        elif block_type == "local_business":
            schema["@type"] = "LocalBusiness"
            schema["name"] = site_name
            schema["url"] = site_url

            if block_value.get("description"):
                schema["description"] = block_value["description"]

            # Process image
            image = block_value.get("image")
            if image:
                image_data = _process_image_block(image, page, request)
                if image_data:
                    schema["image"] = image_data

            # Process address
            address = block_value.get("address")
            if address:
                address_data = _process_address_block(address, page, request)
                if address_data:
                    schema["address"] = address_data

            if block_value.get("telephone"):
                schema["telephone"] = block_value["telephone"]
            if block_value.get("email"):
                schema["email"] = block_value["email"]
            if block_value.get("price_range"):
                schema["priceRange"] = block_value["price_range"]

            # Opening hours
            opening_hours = block_value.get("opening_hours", [])
            if opening_hours:
                schema["openingHours"] = list(opening_hours)

            # Geo coordinates
            lat = block_value.get("geo_latitude")
            lng = block_value.get("geo_longitude")
            if lat and lng:
                schema["geo"] = {
                    "@type": "GeoCoordinates",
                    "latitude": float(lat),
                    "longitude": float(lng),
                }

            # Social media URLs
            same_as = block_value.get("same_as", [])
            if same_as:
                schema["sameAs"] = list(same_as)

        if len(schema) > 2:  # More than just @context and @type
            schemas.append(schema)

    return schemas


def generate_jsonld_for_page(page, request=None):
    """
    Generate all applicable JSON-LD schemas for a page.

    Merges schemas with the following precedence (highest to lowest):
    1. Page-specific override schemas (PageJSONLDOverride)
    2. Page type template schemas (JSONLDSchemaTemplate)
    3. Site-wide schemas (SiteWideJSONLDSchema)

    When the same @type exists at multiple levels, values are merged with
    higher priority schemas overriding lower priority values.

    Also adds auto-generated schemas:
    - BreadcrumbList (from page hierarchy)
    - Language/translation data

    Args:
        page: Wagtail Page instance
        request: Optional request for site-specific values

    Returns:
        List of JSON-LD schema dicts
    """
    from wagtail_seotoolkit.pro.models import (
        JSONLDSchemaTemplate,
        PageJSONLDOverride,
        SiteWideJSONLDSchema,
    )

    page = page.specific
    site = None

    if request:
        from wagtail.models import Site

        site = Site.find_for_request(request)

    # Collect schemas at each level
    site_wide_schemas = []
    template_schemas = []
    page_schemas = []

    # 1. Get site-wide schemas (lowest priority)
    if site:
        try:
            site_schema_obj = SiteWideJSONLDSchema.objects.get(
                site=site, is_active=True
            )
            site_wide_schemas = _convert_site_wide_schemas(
                site_schema_obj.schemas, site, page, request
            )
        except SiteWideJSONLDSchema.DoesNotExist:
            pass

    # 2. Get page type template schemas (medium priority)
    try:
        # First try to get template specific to this content type
        template = JSONLDSchemaTemplate.objects.get(
            content_type=page.content_type, is_active=True
        )
        template_schemas = _convert_streamfield_schemas(template.schemas, page, request)
    except JSONLDSchemaTemplate.DoesNotExist:
        # Fall back to default template (no content type)
        try:
            template = JSONLDSchemaTemplate.objects.get(
                content_type__isnull=True, is_active=True
            )
            template_schemas = _convert_streamfield_schemas(
                template.schemas, page, request
            )
        except JSONLDSchemaTemplate.DoesNotExist:
            pass

    # 3. Get page-specific override schemas (highest priority)
    try:
        override = PageJSONLDOverride.objects.get(page=page, is_active=True)

        if override.use_template:
            # Merge with template schemas
            page_schemas = _convert_streamfield_schemas(override.schemas, page, request)
        else:
            # Use only page schemas, ignore template
            page_schemas = _convert_streamfield_schemas(override.schemas, page, request)
            template_schemas = []  # Clear template schemas
    except PageJSONLDOverride.DoesNotExist:
        pass

    # Merge schemas with precedence: page > template > site-wide
    # Start with site-wide, merge template on top, then page on top
    merged_schemas = _merge_schemas_by_type(site_wide_schemas, template_schemas)
    merged_schemas = _merge_schemas_by_type(merged_schemas, page_schemas)

    # 4. Add auto-generated breadcrumbs (separate, not merged)
    breadcrumb_schema = generate_breadcrumb_jsonld(page, request)
    if breadcrumb_schema:
        # Check if we already have a BreadcrumbList (from page override)
        has_breadcrumb = any(s.get("@type") == "BreadcrumbList" for s in merged_schemas)
        if not has_breadcrumb:
            merged_schemas.append(breadcrumb_schema)

    # 5. Add language schema data to content schemas
    language_data = generate_language_jsonld(page, request)
    if language_data:
        # Add language data to the first content schema (not site-wide types)
        for schema in merged_schemas:
            if schema.get("@type") not in [
                "BreadcrumbList",
                "Organization",
                "WebSite",
                "LocalBusiness",
            ]:
                schema.update(language_data)
                break

    return merged_schemas


def render_jsonld_script(schemas):
    """
    Render JSON-LD schemas as an HTML script tag.

    Args:
        schemas: List of JSON-LD schema dicts

    Returns:
        HTML string with script tag containing JSON-LD
    """
    if not schemas:
        return ""

    # If single schema, don't wrap in array
    if len(schemas) == 1:
        json_str = json.dumps(schemas[0], indent=2, ensure_ascii=False)
    else:
        json_str = json.dumps(schemas, indent=2, ensure_ascii=False)

    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def get_jsonld_placeholders_for_content_type(content_type_id=None):
    """
    Get available placeholders for JSON-LD templates.

    Extends the existing placeholder system with JSON-LD specific fields.

    Args:
        content_type_id: ContentType ID (None for universal placeholders)

    Returns:
        List of placeholder dicts with name, label, type
    """
    from wagtail_seotoolkit.pro.utils.placeholder_utils import (
        get_placeholders_for_content_type,
    )

    # Get base placeholders from existing system
    placeholders = get_placeholders_for_content_type(content_type_id)

    # Add JSON-LD specific placeholders
    jsonld_placeholders = [
        {"name": "full_url", "label": "Full Page URL", "type": "page"},
        {"name": "first_published_at", "label": "First Published Date", "type": "page"},
        {"name": "last_published_at", "label": "Last Published Date", "type": "page"},
    ]

    # Merge, avoiding duplicates
    existing_names = {p["name"] for p in placeholders}
    for p in jsonld_placeholders:
        if p["name"] not in existing_names:
            placeholders.append(p)

    return placeholders


def get_site_wide_placeholders():
    """
    Get available placeholders for site-wide JSON-LD schemas.

    These placeholders are specific to site-wide schemas and include
    site settings data plus basic page fields that are common to all pages.

    Returns:
        List of placeholder dicts with name, label, type
    """
    placeholders = [
        # Site-level placeholders
        {"name": "site_name", "label": "Site Name", "type": "site"},
        {"name": "site_url", "label": "Site URL (root)", "type": "site"},
        # Basic page placeholders (available on any page)
        {"name": "title", "label": "Page Title", "type": "page"},
        {"name": "full_url", "label": "Full Page URL", "type": "page"},
        {"name": "slug", "label": "Page Slug", "type": "page"},
        {"name": "seo_title", "label": "SEO Title", "type": "page"},
        {"name": "search_description", "label": "Meta Description", "type": "page"},
        {"name": "first_published_at", "label": "First Published Date", "type": "page"},
        {"name": "last_published_at", "label": "Last Published Date", "type": "page"},
    ]

    return placeholders
