# Wagtail SEO Toolkit

A comprehensive SEO auditing and optimization plugin for Wagtail CMS that helps you identify and fix SEO issues across your website.

![Dashboard](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/dashboard.png?raw=True)

## 📋 Table of Contents

- [🚀 Features](#-features)
  - [🔍 SEO Best Practices Checks](#-seo-best-practices-checks)
  - [⚡ PageSpeed Insights Checks (Optional)](#-pagespeed-insights-checks-optional)
  - [🎯 Smart Issue Management](#-smart-issue-management)
  - [🔧 Flexible Configuration](#-flexible-configuration)
- [📸 Screenshots](#-screenshots)
- [🛠 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🚀 Usage](#-usage)
  - [Running Audits](#running-audits)
- [🔧 Advanced Configuration](#-advanced-configuration)
- [✉️ Email Notifications & Reporting](#email-notifications--reporting)
- [🛠 Development](#-development)
- [📊 Performance Considerations](#-performance-considerations)
- [📝 Changelog](#-changelog)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

## 🚀 Features

### 🔍 **SEO Best Practices Checks**

- **Title & Meta Tags**: Check for missing, duplicate, or suboptimal meta tags
- **Content Analysis**: Analyze content length, readability, and structure
- **Header Structure**: Validate H1-H6 hierarchy and usage
- **Image Optimization**: Check for missing alt text, proper sizing, and optimization
- **Schema Markup**: Validate structured data implementation
- **Mobile Optimization**: Ensure mobile-friendly design and viewport settings
- **Internal Linking**: Analyze internal link structure and distribution
- **Content Freshness**: Track content publication and modification dates

### ⚡ **PageSpeed Insights Checks** (Optional)

- **Performance Metrics**: Get Core Web Vitals and performance scores
- **Accessibility Checks**: Identify accessibility issues
- **Best Practices**: Check for security and modern web standards
- **SEO Performance**: Analyze technical SEO factors
- **Per-Page-Type Optimization**: Efficiently audit multiple pages of the same type

### 🎯 **Smart Issue Management**

- **Issues Export**: Export list of issues to Excel/CSV
- **Developer vs Content Issues**: Clear distinction between technical and content fixes
- **Historical Reports**: Compare audits over time to track SEO improvements
- **Email Notifications**: Automated email alerts with score changes and new issues

### 🔧 **Flexible Configuration**

- **PageSpeed Settings**: Control API usage and optimization
- **Button Visibility**: Control audit button visibility in admin
- **Dev Fix Filtering**: Show only content-editable issues

### 🤩 **[PRO] Bulk meta editor**

- **Multi-Page Editing**: Edit SEO titles and meta descriptions for hundreds of pages at once instead of manually editing each one
- **Smart Templates**: Use placeholders like `{title} | {site_name}` or `{introduction[:100]}` to create consistent metadata patterns across your site
- **Issue-Based Filtering**: Jump directly to pages with specific SEO issues from the dashboard for quick fixes
- **Live Validation**: Real-time character counting and validation ensures your metadata meets SEO best practices
- **Automatic Template Integration**: Enable middleware to automatically apply bulk editor changes to rendered meta tags without modifying your existing template tags across multiple pages

### 🧬 **[PRO] JSON-LD Schema Editor**

- **Visual Schema Builder**: Create structured data schemas without writing JSON
- **35+ Schema Types**: Article, Product, FAQPage, HowTo, Recipe, Video, and more
- **Smart Templates**: Define schemas per page type with placeholder support like `{title}`, `{first_published_at}`
- **Page Overrides**: Customize schemas for specific pages
- **Site-Wide Schemas**: Configure Organization, WebSite, and LocalBusiness for your entire site
- **Automatic Rendering**: Use middleware or template tag to render schemas

**Template Tag Usage:**

```django
{% load wagtail_seotoolkit_tags %}
{% jsonld_schemas %}
```

**Middleware:** The `SEOMetadataMiddleware` handles both meta tags and JSON-LD schemas automatically.

## 📸 Screenshots

### SEO Dashboard

![Dashboard](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/dashboard.png?raw=True)
_Comprehensive overview of your site's SEO health with actionable insights_

### Issues Report

![Issues View](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/issues_view.png?raw=True)
_Detailed view of all SEO issues with filtering and management options_

### Page Sidebar

![Sidebar](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/sidebar.png?raw=True)

_See issues directly in page edit view_

### Bulk editor

![Bulk editor](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/bulk_editor.png?raw=True)
_Fix multiple meta tag issues at once_

### Comparison report

![Comparison reports](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/comparison_report.png?raw=True)
_Overview of your website historical performance_

###

![Email notifications](https://github.com/wayfdigital/wagtail-seotoolkit/blob/main/static/periodic_email.png?raw=True)
_Reveive email notifications with new and fixed issues_

## 🛠 Installation

### Prerequisites

- Wagtail 6.4+

### Install via pip

```bash
pip install wagtail-seotoolkit
```

### Add to your Django settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'wagtail_seotoolkit',
]
```

### Run migrations

```bash
python manage.py migrate
```

### (Optional) Enable middleware

```python
MIDDLEWARE = [
    ...
    # SEO Toolkit Middleware - Must be after Wagtail's middleware
    "wagtail_seotoolkit.middleware.SEOMetadataMiddleware",
]
```

**How the bulk editor works with middleware:**

The bulk editor works on the basic page fields `seo_title` and `search_description`. When the middleware is enabled, it will replace the rendered meta tags in your HTML output with the new versions applied from the bulk editor. This enables you to start using bulk editor features without modifying all of the template tags across multiple pages - the middleware automatically intercepts and updates the meta tags at render time.

**Placeholder Processing Modes:**

You can control how placeholders (like `{title}`, `{site_name}`, etc.) are processed using the `WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS` setting:

- **`True` (default, recommended)**: Placeholders are stored in the database and processed at runtime by the middleware. This means your SEO metadata stays dynamic - if a page title changes, the SEO title automatically updates. Requires middleware to be enabled.

- **`False`**: Placeholders are processed immediately when saving and the final values are stored in the database. This creates static metadata that won't update if page content changes. Use this if you don't want to use the middleware or need static values.

## ⚙️ Configuration

### All Settings

```python
# settings.py

# SEO Toolkit Configuration
WAGTAIL_SEOTOOLKIT_SHOW_AUDIT_BUTTON = True  # Show audit button in admin, enable only if you have run_scheduled_audits configured to run periodically (default: False) 
WAGTAIL_SEOTOOLKIT_INCLUDE_DEV_FIXES = True  # Include developer-required fixes (default: True)

# Bulk Editor / Middleware Configuration
WAGTAIL_SEOTOOLKIT_PROCESS_PLACEHOLDERS = True  # Process placeholders at runtime via middleware (default: True)
                                                  # If False, placeholders are processed once when saving

# Email & Reporting Configuration
WAGTAIL_SEOTOOLKIT_REPORT_EMAIL_RECIPIENTS = [  # List of emails to receive audit reports, leave blank to disable email notifications
    'seo-team@example.com',
    'marketing@example.com',
]
WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL = "7d"  # How often to generate compariosn reports (default: "7d")
                                            # Formats: "7d" (days), "2w" (weeks), "1m" (months)

# Email notifications require Django's standard email settings (EMAIL_HOST, EMAIL_PORT, etc.) - see Django documentation

# PageSpeed Insights Configuration (Optional - must be manually enabled)
# Note: PageSpeed checks are disabled by default and must be manually enabled
WAGTAIL_SEOTOOLKIT_PAGESPEED_API_KEY = "your-api-key-here"  # Get from Google
WAGTAIL_SEOTOOLKIT_PAGESPEED_ENABLED = True  # Enable PageSpeed checks
WAGTAIL_SEOTOOLKIT_PAGESPEED_DRY_RUN = False  # Use real API calls
WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE = True  # Optimize API usage
```

### Getting a PageSpeed API Key

1. Visit [Google PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
2. Create a new project or select existing one
3. Enable the PageSpeed Insights API
4. Create credentials (API key)
5. Add the key to your settings

## 🚀 Usage

### Running Audits

This plugin exposes 2 management commands `seoaudit` and `run_scheduled_audits` those commands needs to be executed by some process. Smiliarly to [publish_scheduled](https://docs.wagtail.org/en/stable/reference/management_commands.html#publish-scheduled).

#### Option 1: User-Requested Audits (Recommended)

To allow users to request audits through the admin interface:

1. **Enable the audit button**:

   ```python
   # settings.py
   WAGTAIL_SEOTOOLKIT_SHOW_AUDIT_BUTTON = True
   ```

2. **Set up periodic task** to process scheduled audits:
   ```bash
   python manage.py run_scheduled_audits
   ```
   WARNING: First audit needs to be started manually with `seoaudit` command.

#### Option 2: Automated Audits

Set up a scheduled task to run audits automatically:

```bash
python manage.py seoaudit
```

## 🔧 Advanced Configuration

### Email Notifications & Historical Reporting

Wagtail SEO Toolkit can automatically generate comparison reports between audits and send email notifications to your team.

#### Configuring Email Settings

Email notifications require Django's standard email settings (EMAIL_HOST, EMAIL_PORT, etc.) - see Django documentation

#### Configuring Report Email Recipients

Set who should receive audit report emails:

```python
# settings.py

# List of email addresses to receive audit reports
# Leave blank to disable email messages
WAGTAIL_SEOTOOLKIT_REPORT_EMAIL_RECIPIENTS = [
    'seo-team@example.com',
    'marketing@example.com',
    'admin@example.com',
]
```

Email notifications are an optional feature. If you leave the recipients list blank no emails will be sent.

#### What Gets Emailed?

When a report is generated, the email includes:

- **Score Change**: Visual indicator showing if your SEO score improved, declined, or stayed the same
- **New Issues Summary**:
  - Total new issues detected
  - New issues on existing pages
  - New issues on newly created pages
- **Top 20 New Issues**: Detailed list of the most important new issues, sorted by severity
- **Call to Action**: Link to view the full detailed report in your admin dashboard

#### Configuring Report Interval

Even if you opt out of email notifications, the toolkit will create comparisson reports accessible from admin. Showing you historical performance, new and fixed issues in this time period.
Control how often comparison reports are generated:

```python
# settings.py

# Generate reports every 7 days (default)
WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL = "7d"

# Other examples:
# WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL = "1d"   # Daily reports
# WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL = "2w"   # Every 2 weeks
# WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL = "1m"   # Monthly reports
```

**Supported interval formats:**

- `d` - days (e.g., `7d` = 7 days)
- `w` - weeks (e.g., `2w` = 2 weeks)
- `m` - months (e.g., `1m` = ~30 days)



### Filtering Dev Fixes

For content editors who shouldn't see technical issues:

```python
# settings.py
WAGTAIL_SEOTOOLKIT_INCLUDE_DEV_FIXES = False
```

This will hide all issues that require developer intervention, showing only content-related issues.

### PageSpeed Optimization

The `WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE` setting optimizes PageSpeed API usage for sites with many pages of the same type:

```python
# settings.py
WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE = True  # Enable optimization (default: False)
```

**How it works:**

- **When `True`**: Tests PageSpeed on only one page per page type (e.g., one BlogPage, one ProductPage)
- **When `False`**: Tests PageSpeed on every individual page
- **Result propagation**: PageSpeed issues found on the test page are applied to all pages of that same type

**Example:**

- Site has 50 BlogPage instances and 30 ProductPage instances
- **With optimization**: 2 PageSpeed API calls (1 for BlogPage + 1 for ProductPage)
- **Without optimization**: 80 PageSpeed API calls (1 for each page)

**Benefits:**

- **Cost savings**: Dramatically reduces Google PageSpeed API usage
- **Faster audits**: Significantly faster completion times
- **Same accuracy**: PageSpeed issues are typically consistent across pages of the same type

**When to use:**

- Sites with many pages of the same type
- When PageSpeed API costs are a concern
- For faster audit execution

## 🛠 Development

### Setting up Development Environment

You can start developing with this plugin using the [bakerydemo](https://github.com/wagtail/bakerydemo) project that includes this plugin enabled:

```bash
# Clone the repository
git clone https://github.com/your-org/wagtail-seotoolkit.git
cd wagtail-seotoolkit

# Start the development environment with Docker
docker-compose up

# The plugin will be available at http://localhost:8000/admin/
# Login with: admin / changeme
```

## 📊 Performance Considerations

### PageSpeed API Limits

- Google PageSpeed Insights API has rate limits
- Use `WAGTAIL_SEOTOOLKIT_PAGESPEED_PER_PAGE_TYPE = True` for large sites
- Consider running audits during off-peak hours

---

## 🗺️ Roadmap

We are in the **Phase 2** - free tier showing you what's broken and first pro feature Bulk editor.

### ✅ Recently Released

- **Historical Tracking** - See how your SEO health improves over time with comparison reports
- **Email Alerts** - Automated email notifications when audits detect changes

### Coming Very Soon (Phase 2 Further development - Pro Tier)

- **JSON-LD Editor** - Visual editor for structured data

### Coming Also Quite Soon (Phase 3 - AI)

- **AI-Powered Optimization** - GPT-generated meta descriptions optimized for search
- **Smart Internal Linking** - Automatic suggestions for related content
- **Content Scoring** - AI analysis for search visibility and user engagement
- **Competitive Analysis** - See how your pages compare to competitors

**Interested in Pro features?** Let us know what would be most valuable → [GitHub Discussions](https://github.com/wayfdigital/wagtail-seotoolkit/discussions)

---

## 🤝 Contributing

This is an early release and we want your feedback!

**Found a bug?** [Open an issue](https://github.com/wayfdigital/wagtail-seotoolkit/issues)

**Have a suggestion?** [Start a discussion](https://github.com/wayfdigital/wagtail-seotoolkit/discussions)

### What We're Looking For Feedback On:

- Are the checks finding real, actionable issues?
- What SEO checks are we missing?
- Does the bulk fixing is worth paying for?
- How's the performance on large sites (1000+ pages)?

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/wayfdigital/wagtail-seotoolkit/issues)
- **Discussions:** [GitHub Discussions](https://github.com/wayfdigital/wagtail-seotoolkit/discussions)
- **Email:** hello@wayfdigital.com

---

## 📝 Changelog

### Version 0.1.1

- Initial release
- Comprehensive SEO auditing
- PageSpeed Insights integration
- Wagtail admin integration
- Configurable settings

### Version 0.1.2

- Fix CSRF bug

### Version 0.1.3

- Further improvements to CSRF fixes

### Version 0.2.0

- First pro feature - Bulk editor!
- Subscription management from the plugin
- License update

### Version 0.2.1

- README update

### Version 0.2.2

- Bulk editor fixes

### Version 0.2.3

- Fix checks bypassing the middleware processing resulting in false positives


---

## 📄 License

This project uses **dual licensing**:

### Core Features (MIT License)

The following features are licensed under the **MIT License** and are **free and open source**:

- ✅ SEO audit engine and all checkers (title, meta, content, headers, images, schema, mobile, links, freshness, PageSpeed)
- ✅ Management commands (`seoaudit`, `run_scheduled_audits`)
- ✅ SEO audit models and data structures
- ✅ Dashboard and issues reporting (read-only views)
- ✅ Side panels showing SEO checks on page editor

**License:** See [LICENSE-MIT](LICENSE-MIT) for full MIT license text.

### Pro Features (WAYF Proprietary License)

The following features require a **paid subscription** and are licensed under the **WAYF Proprietary License**:

- 🔒 **Bulk Metadata Editor** - Edit SEO titles and meta descriptions for hundreds of pages at once
- 🔒 **SEO Templates** - Create reusable metadata templates with placeholders
- 🔒 **Metadata Middleware** - Automatically apply bulk editor changes to rendered pages
- 🔒 **Subscription Management** - License verification and instance management
- 🔒 **Advanced Placeholder System** - Dynamic field placeholders for metadata templates

**License:** See [LICENSE-PROPRIETARY](LICENSE-PROPRIETARY) for full proprietary license terms.

**Source Available:** The source code for pro features is available for reference, security review, and transparency, but modification and redistribution are prohibited without permission from WAYF.

### Usage Rights

- ✅ **Core features:** Free to use, modify, and redistribute under MIT license
- ✅ **Pro features:** Free to use with a valid subscription, but modification and redistribution are restricted
- ✅ **Commercial use:** Both core and pro features can be used in commercial projects
- ✅ **Contributions:** Welcome for core features; pro feature contributions require WAYF approval (see [CONTRIBUTING.md](CONTRIBUTING.md))

### Getting a Pro License

Pro features require an active subscription. You can obtain the pro license directly from the plugin UI after installation.

**Author:** [WAYF](https://wayfdigital.com)

**Copyright:** ©2025 WAYF DIGITAL SP. Z O.O.

---

## 🙏 Acknowledgments

- Built for the Wagtail CMS community
- Inspired by modern SEO best practices
- Special thanks to early testers and contributors
- Special thanks to all the contributors to the [bakerydemo](https://github.com/wagtail/bakerydemo)
  - Bakery demo is used only for the development environment for this project, it's not redistributed with the package

---

**⭐ If this tool saves you time, please star the repo and share it with other Wagtail users!**

Made with ❤️ by [WAYF](https://wayfdigital.com/)

**About WAYF:** We build tools for modern web development. Check out our other projects at [wayfdigital.com](https://wayfdigital.com/)
