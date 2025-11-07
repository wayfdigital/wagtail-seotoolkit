"""
Content freshness checker.

Checks for publish dates, modified dates, and content age.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from wagtail_seotoolkit.core.models import SEOAuditIssueType

from wagtail_seotoolkit.core.utils.checkers.base import BaseChecker

# Content freshness constraints
MAX_CONTENT_AGE_DAYS = 365


class FreshnessChecker(BaseChecker):
    """Checker for content freshness."""

    def check(self) -> List[Dict[str, Any]]:
        """Check for content freshness issues."""
        self.issues = []

        # Check for published date
        published_meta = self._find_published_date_meta()
        published_date, has_published_schema = self._find_published_date_schema()

        if not published_meta and not has_published_schema:
            self.add_issue(
                SEOAuditIssueType.CONTENT_NO_PUBLISH_DATE,
                SEOAuditIssueType.get_severity(
                    SEOAuditIssueType.CONTENT_NO_PUBLISH_DATE
                ),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_NO_PUBLISH_DATE
                ),
            )

        # Check for modified date
        modified_meta = self._find_modified_date_meta()
        has_modified_schema = self._has_modified_date_schema()

        if not modified_meta and not has_modified_schema:
            self.add_issue(
                SEOAuditIssueType.CONTENT_NO_MODIFIED_DATE,
                SEOAuditIssueType.get_severity(
                    SEOAuditIssueType.CONTENT_NO_MODIFIED_DATE
                ),
                SEOAuditIssueType.get_description_template(
                    SEOAuditIssueType.CONTENT_NO_MODIFIED_DATE
                ),
            )

        # Check if content is old
        if published_date:
            days_old = (datetime.now(published_date.tzinfo) - published_date).days
            if days_old > MAX_CONTENT_AGE_DAYS:
                self.add_issue(
                    SEOAuditIssueType.CONTENT_NOT_UPDATED,
                    SEOAuditIssueType.get_severity(
                        SEOAuditIssueType.CONTENT_NOT_UPDATED
                    ),
                    SEOAuditIssueType.get_description_template(
                        SEOAuditIssueType.CONTENT_NOT_UPDATED
                    ).format(days_old=days_old),
                )

        return self.issues

    def _find_published_date_meta(self):
        """Find published date in meta tags."""
        return (
            self.soup.find("meta", attrs={"property": "article:published_time"})
            or self.soup.find("meta", attrs={"name": "publish_date"})
            or self.soup.find("meta", attrs={"name": "date"})
        )

    def _find_modified_date_meta(self):
        """Find modified date in meta tags."""
        return self.soup.find(
            "meta", attrs={"property": "article:modified_time"}
        ) or self.soup.find("meta", attrs={"name": "last-modified"})

    def _find_published_date_schema(self) -> tuple:
        """Find published date in JSON-LD schema."""
        json_ld_scripts = self.soup.find_all("script", type="application/ld+json")
        has_published_schema = False
        published_date = None

        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]

                for item in schema_data:
                    if "datePublished" in item:
                        has_published_schema = True
                        try:
                            published_date = datetime.fromisoformat(
                                item["datePublished"].replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            pass
                        break
            except (json.JSONDecodeError, AttributeError):
                pass

        return published_date, has_published_schema

    def _has_modified_date_schema(self) -> bool:
        """Check if modified date exists in JSON-LD schema."""
        json_ld_scripts = self.soup.find_all("script", type="application/ld+json")

        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]

                for item in schema_data:
                    if "dateModified" in item:
                        return True
            except (json.JSONDecodeError, AttributeError):
                pass

        return False
