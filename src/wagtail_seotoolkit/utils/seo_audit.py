"""
SEO Audit utilities for analyzing HTML pages and detecting SEO issues.
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from tqdm import tqdm

# ==================== Constants ====================

# Title tag constraints
TITLE_MIN_LENGTH = 50
TITLE_MAX_LENGTH = 60

# Meta description constraints
META_DESC_MIN_LENGTH = 120
META_DESC_MAX_LENGTH = 160
CTA_KEYWORDS = ['buy', 'learn', 'discover', 'get', 'find', 'explore', 'download', 'try', 'start', 'join']

# Content constraints
MIN_WORD_COUNT = 300
MIN_WORDS_FOR_PARAGRAPHS = 100

# Image alt text constraints
GENERIC_ALT_TEXTS = ['image', 'photo', 'picture', 'img', 'icon']
MAX_ALT_LENGTH = 125

# Schema types
ORGANIZATION_SCHEMA_TYPES = {'Organization', 'Person', 'LocalBusiness'}
ARTICLE_SCHEMA_TYPES = {'Article', 'BlogPosting', 'NewsArticle', 'ScholarlyArticle'}

# Internal linking constraints
MIN_INTERNAL_LINKS = 3

# Content freshness constraints
MAX_CONTENT_AGE_DAYS = 365

# Scoring
SCORE_PENALTY_PER_ISSUE = 5


# ==================== Helper Functions ====================

def extract_base_domain(url: str) -> str:
    """Extract base domain from a URL."""
    if not url:
        return ""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def is_content_page(soup: BeautifulSoup, min_words: int = MIN_WORD_COUNT) -> bool:
    """Check if page is a content page based on word count."""
    body = soup.find('body')
    if not body:
        return False
    text_content = body.get_text(separator=' ', strip=True)
    return count_words(text_content) > min_words


# ==================== SEO Auditor Class ====================

class SEOAuditor:
    """Main SEO auditor class that runs all checks on HTML content."""
    
    def __init__(self, html: str, url: str = "", base_domain: str = ""):
        """
        Initialize the auditor with HTML content.
        
        Args:
            html: The HTML content to audit
            url: The URL of the page being audited
            base_domain: The base domain to identify internal links
        """
        self.html = html
        self.url = url
        self.base_domain = base_domain or extract_base_domain(url)
        self.soup = BeautifulSoup(html, 'html.parser')
        self.issues: List[Dict[str, Any]] = []
    
    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Run all SEO checks and return a list of issues."""
        self.issues = []
        
        # Run all checks
        self.check_title_tag()
        self.check_meta_description()
        self.check_content_depth()
        self.check_header_structure()
        self.check_image_alt_text()
        self.check_structured_data()
        self.check_mobile_responsiveness()
        self.check_internal_linking()
        self.check_content_freshness()
        
        return self.issues
    
    def add_issue(self, issue_type: str, severity: str, description: str) -> None:
        """Add an issue to the issues list."""
        self.issues.append({
            'issue_type': issue_type,
            'issue_severity': severity,
            'description': description,
            'page_url': self.url,
        })
    
    # ==================== Title Tag Optimization ====================
    
    def check_title_tag(self) -> None:
        """Check for title tag issues."""
        title_tag = self.soup.find('title')
        
        if not title_tag or not title_tag.string:
            self.add_issue(
                'title_missing',
                'high',
                'Page is missing a title tag. This is critical for SEO as title tags are the #1 on-page SEO factor.'
            )
            return
        
        title_text = title_tag.string.strip()
        title_length = len(title_text)
        
        if title_length < TITLE_MIN_LENGTH:
            self.add_issue(
                'title_too_short',
                'medium',
                f'Title tag is too short ({title_length} chars). Recommended: {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH} characters. Current title: "{title_text}"'
            )
        elif title_length > TITLE_MAX_LENGTH:
            self.add_issue(
                'title_too_long',
                'medium',
                f'Title tag is too long ({title_length} chars). It may be truncated in search results. Recommended: {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH} characters.'
            )
    
    # ==================== Meta Description Quality ====================
    
    def check_meta_description(self) -> None:
        """Check for meta description issues."""
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        
        if not meta_desc or not meta_desc.get('content'):
            self.add_issue(
                'meta_description_missing',
                'high',
                'Page is missing a meta description. This impacts click-through rate in search results and AI Overviews context.'
            )
            return
        
        desc_text = meta_desc.get('content', '').strip()
        desc_length = len(desc_text)
        
        if desc_length < META_DESC_MIN_LENGTH:
            self.add_issue(
                'meta_description_too_short',
                'medium',
                f'Meta description is too short ({desc_length} chars). Recommended: {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH} characters.'
            )
        elif desc_length > META_DESC_MAX_LENGTH:
            self.add_issue(
                'meta_description_too_long',
                'medium',
                f'Meta description is too long ({desc_length} chars). It may be truncated in search results. Recommended: {META_DESC_MIN_LENGTH}-{META_DESC_MAX_LENGTH} characters.'
            )
        
        # Check for CTA words
        if not any(word in desc_text.lower() for word in CTA_KEYWORDS):
            self.add_issue(
                'meta_description_no_cta',
                'low',
                f'Meta description lacks call-to-action words (e.g., {", ".join(CTA_KEYWORDS[:5])}). Adding CTAs can improve click-through rates.'
            )
    
    # ==================== Content Depth Analysis ====================
    
    def check_content_depth(self) -> None:
        """Check for content depth issues."""
        # Get main content - try to find main, article, or body content
        main_content = self.soup.find('main') or self.soup.find('article') or self.soup.find('body')
        
        if not main_content:
            self.add_issue(
                'content_empty',
                'high',
                'Page has no discernible content. Empty pages rarely rank in search results.'
            )
            return
        
        # Remove non-content elements
        content_copy = main_content.__copy__()
        for element in content_copy.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Get text content
        text_content = content_copy.get_text(separator=' ', strip=True)
        word_count = count_words(text_content)
        
        if word_count == 0:
            self.add_issue(
                'content_empty',
                'high',
                'Page has no text content. Empty pages rarely rank in search results.'
            )
            return
        
        if word_count < MIN_WORD_COUNT:
            self.add_issue(
                'content_thin',
                'medium',
                f'Page has thin content ({word_count} words). Recommended: at least {MIN_WORD_COUNT} words. AI Overviews favor comprehensive content.'
            )
        
        # Check for paragraphs
        paragraphs = content_copy.find_all('p')
        if word_count > MIN_WORDS_FOR_PARAGRAPHS and len(paragraphs) == 0:
            self.add_issue(
                'content_no_paragraphs',
                'low',
                'Content lacks paragraph structure. Breaking content into paragraphs improves readability and user experience.'
            )
    
    # ==================== Header Structure ====================
    
    def check_header_structure(self) -> None:
        """Check for header structure issues."""
        h1_tags = self.soup.find_all('h1')
        
        if len(h1_tags) == 0:
            self.add_issue(
                'header_no_h1',
                'high',
                'Page is missing an H1 tag. H1 tags are critical for SEO and help search engines understand page content.'
            )
        elif len(h1_tags) > 1:
            self.add_issue(
                'header_multiple_h1',
                'medium',
                f'Page has {len(h1_tags)} H1 tags. Best practice is to have exactly one H1 per page.'
            )
        
        # Check for subheadings on content pages
        if is_content_page(self.soup):
            h2_tags = self.soup.find_all('h2')
            h3_tags = self.soup.find_all('h3')
            
            if len(h2_tags) == 0 and len(h3_tags) == 0:
                body = self.soup.find('body')
                word_count = count_words(body.get_text(separator=' ', strip=True)) if body else 0
                self.add_issue(
                    'header_no_subheadings',
                    'medium',
                    f'Page has {word_count} words but no H2 or H3 subheadings. Headers help structure content for users and search engines.'
                )
        
        # Check header hierarchy
        self._check_header_hierarchy()
    
    def _check_header_hierarchy(self) -> None:
        """Check if header hierarchy is properly maintained."""
        headers = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headers) <= 1:
            return
        
        prev_level = 0
        for header in headers:
            current_level = int(header.name[1])
            if prev_level > 0 and current_level > prev_level + 1:
                self.add_issue(
                    'header_broken_hierarchy',
                    'low',
                    f'Header hierarchy is broken: found {header.name.upper()} after H{prev_level}. Headers should follow sequential order (H1→H2→H3).'
                )
                break
            prev_level = current_level
    
    # ==================== Image Alt Text ====================
    
    def check_image_alt_text(self) -> None:
        """Check for image alt text issues."""
        images = self.soup.find_all('img')
        images_without_alt = 0
        
        for img in images:
            alt_text = img.get('alt', '').strip()
            
            if not alt_text:
                images_without_alt += 1
            else:
                # Check for generic alt
                if alt_text.lower() in GENERIC_ALT_TEXTS:
                    self.add_issue(
                        'image_alt_generic',
                        'low',
                        f'Image has generic alt text: "{alt_text}". Alt text should be descriptive and meaningful.'
                    )
                
                # Check for too long alt
                if len(alt_text) > MAX_ALT_LENGTH:
                    self.add_issue(
                        'image_alt_too_long',
                        'low',
                        f'Image alt text is too long ({len(alt_text)} chars). Recommended: under {MAX_ALT_LENGTH} characters.'
                    )
        
        if images_without_alt > 0:
            self.add_issue(
                'image_no_alt',
                'medium',
                f'{images_without_alt} image(s) are missing alt text. Alt text is critical for accessibility and helps images rank in Google Images.'
            )
    
    # ==================== Structured Data Presence ====================
    
    def check_structured_data(self) -> None:
        """Check for structured data issues."""
        json_ld_scripts = self.soup.find_all('script', type='application/ld+json')
        
        if len(json_ld_scripts) == 0:
            self.add_issue(
                'schema_missing',
                'high',
                'Page has no Schema markup (JSON-LD). AI Overviews and Google rely on structured data to understand content.'
            )
            return
        
        schema_types = self._parse_schema_types(json_ld_scripts)
        
        # Check for Organization/Person
        if not schema_types.intersection(ORGANIZATION_SCHEMA_TYPES):
            self.add_issue(
                'schema_no_organization',
                'medium',
                'Page is missing Organization/Person schema. This helps establish entity relationships and trust signals.'
            )
        
        # Check for Article/BlogPosting on content pages
        if is_content_page(self.soup) and not schema_types.intersection(ARTICLE_SCHEMA_TYPES):
            self.add_issue(
                'schema_no_article',
                'medium',
                'Content page is missing Article/BlogPosting schema. This helps with rich results and AI Overview citations.'
            )
    
    def _parse_schema_types(self, json_ld_scripts) -> set:
        """Parse and validate JSON-LD scripts, returning schema types."""
        schema_types = set()
        
        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                
                # Handle both single objects and arrays
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]
                
                for item in schema_data:
                    if '@type' in item:
                        schema_type = item['@type']
                        if isinstance(schema_type, list):
                            schema_types.update(schema_type)
                        else:
                            schema_types.add(schema_type)
            except (json.JSONDecodeError, AttributeError):
                self.add_issue(
                    'schema_invalid',
                    'high',
                    'Page has invalid JSON-LD structured data. Fix syntax errors to ensure search engines can parse your schema.'
                )
        
        return schema_types
    
    # ==================== Mobile Responsiveness ====================
    
    def check_mobile_responsiveness(self) -> None:
        """Check for mobile responsiveness issues."""
        # Check for viewport meta tag
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        
        if not viewport:
            self.add_issue(
                'mobile_no_viewport',
                'high',
                'Page is missing viewport meta tag. This is essential for mobile-first indexing. Add: <meta name="viewport" content="width=device-width, initial-scale=1">'
            )
        
        # Check for fixed-width layouts
        self._check_fixed_width_layout()
        
    
    def _check_fixed_width_layout(self) -> None:
        """Check if page uses fixed-width layout."""
        fixed_width_pattern = re.compile(r'width\s*:\s*\d+px')
        
        # Check body or main container with fixed width
        body_tag = self.soup.find('body')
        main_containers = self.soup.find_all(
            ['div', 'main', 'section'],
            id=re.compile(r'(container|wrapper|main)', re.I),
            limit=5
        )
        
        for container in [body_tag] + main_containers:
            if container and container.get('style'):
                if fixed_width_pattern.search(container.get('style', '')):
                    self.add_issue(
                        'mobile_fixed_width',
                        'medium',
                        'Page appears to use fixed-width layout. Use responsive design with relative units (%, em, rem) for better mobile experience.'
                    )
                    break
    

    # ==================== Internal Linking ====================
    
    def check_internal_linking(self) -> None:
        """Check for internal linking issues."""
        all_links = self.soup.find_all('a', href=True)
        
        if len(all_links) == 0:
            return  # No links at all - not necessarily an issue
        
        internal_links, external_links = self._categorize_links(all_links)
        
        # Check for no internal links
        if len(internal_links) == 0:
            if len(external_links) > 0:
                self.add_issue(
                    'internal_links_all_external',
                    'medium',
                    f'Page has {len(external_links)} external links but no internal links. Internal links help Google understand site structure.'
                )
            else:
                self.add_issue(
                    'internal_links_none',
                    'medium',
                    'Page has no internal links. Internal linking is critical for topical authority and helping users navigate your site.'
                )
        elif len(internal_links) < MIN_INTERNAL_LINKS and is_content_page(self.soup):
            self.add_issue(
                'internal_links_few',
                'low',
                f'Content page has only {len(internal_links)} internal link(s). Recommended: at least {MIN_INTERNAL_LINKS} internal links for better site structure.'
            )
    
    def _categorize_links(self, links) -> tuple:
        """Categorize links into internal and external."""
        internal_links = []
        external_links = []
        
        for link in links:
            href = link.get('href', '').strip()
            
            # Skip empty, anchor, and javascript links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Determine if internal or external
            if href.startswith('/') or (self.base_domain and self.base_domain in href):
                internal_links.append(link)
            elif href.startswith('http'):
                external_links.append(link)
            else:
                # Relative link - consider internal
                internal_links.append(link)
        
        return internal_links, external_links
    
    # ==================== Content Freshness ====================
    
    def check_content_freshness(self) -> None:
        # Check for published date
        published_meta = self._find_published_date_meta()
        published_date, has_published_schema = self._find_published_date_schema()
        
        if not published_meta and not has_published_schema:
            self.add_issue(
                'content_no_publish_date',
                'low',
                'Content page is missing published date metadata. Add article:published_time meta tag or datePublished in schema.'
            )
        
        # Check for modified date
        modified_meta = self._find_modified_date_meta()
        has_modified_schema = self._has_modified_date_schema()
        
        if not modified_meta and not has_modified_schema:
            self.add_issue(
                'content_no_modified_date',
                'low',
                'Content page is missing last modified date. Add article:modified_time meta tag or dateModified in schema for time-sensitive content.'
            )
        
        # Check if content is old
        if published_date:
            days_old = (datetime.now(published_date.tzinfo) - published_date).days
            if days_old > MAX_CONTENT_AGE_DAYS:
                self.add_issue(
                    'content_not_updated',
                    'low',
                    f'Content was published {days_old} days ago and may need updating. Google favors fresh content for time-sensitive queries.'
                )
    
    def _find_published_date_meta(self):
        """Find published date in meta tags."""
        return (
            self.soup.find('meta', attrs={'property': 'article:published_time'}) or
            self.soup.find('meta', attrs={'name': 'publish_date'}) or
            self.soup.find('meta', attrs={'name': 'date'})
        )
    
    def _find_modified_date_meta(self):
        """Find modified date in meta tags."""
        return (
            self.soup.find('meta', attrs={'property': 'article:modified_time'}) or
            self.soup.find('meta', attrs={'name': 'last-modified'})
        )
    
    def _find_published_date_schema(self) -> tuple:
        """Find published date in JSON-LD schema."""
        json_ld_scripts = self.soup.find_all('script', type='application/ld+json')
        has_published_schema = False
        published_date = None
        
        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]
                
                for item in schema_data:
                    if 'datePublished' in item:
                        has_published_schema = True
                        try:
                            published_date = datetime.fromisoformat(
                                item['datePublished'].replace('Z', '+00:00')
                            )
                        except (ValueError, AttributeError):
                            pass
                        break
            except (json.JSONDecodeError, AttributeError):
                pass
        
        return published_date, has_published_schema
    
    def _has_modified_date_schema(self) -> bool:
        """Check if modified date exists in JSON-LD schema."""
        json_ld_scripts = self.soup.find_all('script', type='application/ld+json')
        
        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                if isinstance(schema_data, dict):
                    schema_data = [schema_data]
                
                for item in schema_data:
                    if 'dateModified' in item:
                        return True
            except (json.JSONDecodeError, AttributeError):
                pass
        
        return False


# ==================== Page Rendering ====================

def get_page_html(page) -> str:
    """
    Get HTML content for a Wagtail page.
    
    Attempts to render the page using Wagtail's render method.
    
    Args:
        page: The Wagtail page to get HTML from
        
    Returns:
        HTML string
    """
    try:
        # Get the rendered content from the page
        request = HttpRequest()
        # Add necessary attributes to the request
        site = page.get_site()
        request.META = {"SERVER_NAME": site.hostname, "SERVER_PORT": site.port}
        request.path = page.url
        request.user = AnonymousUser()
        rendered_content = page.serve(request).render()
        if isinstance(rendered_content.content, bytes):
            return rendered_content.content.decode("utf-8")
        else:
            return str(rendered_content.content)
    except Exception as e:
        # Use tqdm.write to avoid breaking the progress bar
        tqdm.write(f"  ⚠️  Could not render {page.title}: {e}")
    

# ==================== Audit Execution ====================

def audit_single_page(page, audit_run) -> List[Dict[str, Any]]:
    """
    Audit a single Wagtail page and create issue records.
    
    Args:
        page: The Wagtail page to audit
        audit_run: The SEOAuditRun instance to attach issues to
        
    Returns:
        List of issues found
    """
    from wagtail_seotoolkit.models import SEOAuditIssue
    
    # Get HTML content
    html = get_page_html(page)
    
    # Get page URL and base domain
    url = page.get_full_url() if hasattr(page, 'get_full_url') else page.url
    base_domain = extract_base_domain(url)
    
    # Run audit
    auditor = SEOAuditor(html, url=url, base_domain=base_domain)
    issues = auditor.run_all_checks()
    
    # Create issue records
    for issue_data in issues:
        SEOAuditIssue.objects.create(
            audit_run=audit_run,
            issue_type=issue_data['issue_type'],
            issue_severity=issue_data['issue_severity'],
            page_url=issue_data.get('page_url', ''),
            page_title=page.title,
            description=issue_data['description']
        )
    
    return issues


def run_audit_on_pages(pages: List, audit_run, show_progress: bool = True) -> Dict[str, Any]:
    """
    Run SEO audit on a list of Wagtail pages.
    
    Args:
        pages: List of Wagtail pages to audit
        audit_run: The SEOAuditRun instance to attach issues to
        show_progress: Whether to show a progress bar
        
    Returns:
        Dictionary with audit results summary
    """
    total_pages = len(pages)
    total_issues = 0
    
    # Audit each page
    if show_progress:
        total_issues = _audit_with_progress(pages, audit_run)
    else:
        for page in pages:
            issues = audit_single_page(page, audit_run)
            total_issues += len(issues)
    
    # Calculate and save results
    overall_score = calculate_audit_score(total_issues, total_pages)
    audit_run.status = 'completed'
    audit_run.overall_score = overall_score
    audit_run.pages_analyzed = total_pages
    audit_run.save()
    
    # Get breakdown by severity
    return {
        'total_pages': total_pages,
        'total_issues': total_issues,
        'overall_score': overall_score,
        'high_issues': audit_run.issues.filter(issue_severity='high').count(),
        'medium_issues': audit_run.issues.filter(issue_severity='medium').count(),
        'low_issues': audit_run.issues.filter(issue_severity='low').count(),
    }


def _audit_with_progress(pages: List, audit_run) -> int:
    """Audit pages with a progress bar."""
    total_issues = 0
    
    with tqdm(total=len(pages), desc="Auditing pages", unit="page") as pbar:
        for page in pages:
            pbar.set_description(f"Auditing: {page.title[:50]}")
            
            issues = audit_single_page(page, audit_run)
            total_issues += len(issues)
            
            pbar.set_postfix({"issues": total_issues})
            pbar.update(1)
    
    return total_issues


def calculate_audit_score(total_issues: int, total_pages: int) -> int:
    """
    Calculate an overall SEO score based on issues found.
    
    Score calculation:
    - 0 issues = 100
    - 1 issue per page = 95
    - 5 issues per page = 75
    - 10 issues per page = 50
    - 20+ issues per page = 0
    
    Args:
        total_issues: Total number of issues found
        total_pages: Total number of pages audited
        
    Returns:
        Score from 0-100
    """
    if total_pages == 0:
        return 100
    
    avg_issues = total_issues / total_pages
    score = max(0, 100 - (avg_issues * SCORE_PENALTY_PER_ISSUE))
    
    return int(score)
