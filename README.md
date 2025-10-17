# Wagtail SEO Toolkit

A comprehensive SEO toolkit for Wagtail CMS that provides essential SEO features and optimizations for your Wagtail websites.

**Minimum requirements:**
- Python 3.8+
- Django 3.2+
- Wagtail 5.0+


## Development Setup

This project includes a full development environment using Docker with the [Wagtail Bakerydemo](https://github.com/wagtail/bakerydemo) as the test project. The plugin is automatically configured and ready to use in the demo. The project has the bakery demo frozen at the time of the repo creation.

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/wagtail-seotoolkit.git
cd wagtail-seotoolkit
```

2. **Start the Docker environment:**

```bash
docker compose up --build
```

That's it! The entrypoint script automatically:
- Installs the package in editable mode
- Waits for the database to be ready
- Runs migrations
- Loads bakerydemo initial data (first time only)
- Starts the development server

3. **Access the site:**

Once you see `"Starting development server at http://0.0.0.0:8000/"`, visit:

- **Website**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Credentials**: `admin` / `changeme`

You'll see the **"SEO Toolkit"** menu item (with cog icon) in the Wagtail admin sidebar!

## Features

### SEO Audit

Run comprehensive SEO audits on your Wagtail pages to identify and fix SEO issues:

- **Title Tag Optimization** - Check for missing, too short, or too long titles
- **Meta Description Quality** - Validate descriptions and check for CTAs
- **Content Depth Analysis** - Ensure adequate word count and paragraph structure
- **Header Structure** - Validate H1 usage and heading hierarchy
- **Image Alt Text** - Check for missing or generic alt text
- **Structured Data** - Verify JSON-LD schema markup presence
- **Mobile Responsiveness** - Check viewport meta tag and fixed-width layouts
- **Internal Linking** - Analyze internal link structure
- **Content Freshness** - Check for publish and modified dates

### Running SEO Audits

#### Command Line

Run an SEO audit using the management command:

```bash
# Audit all pages
python manage.py seoaudit

# Audit a specific page
python manage.py seoaudit --page-id 123

# Limit number of pages
python manage.py seoaudit --pages 10

# Disable progress bar
python manage.py seoaudit --no-progress
```

### Development Workflow

The development environment is configured with **live code reloading**:

1. Edit package code in `src/wagtail_seotoolkit/`
2. Save your changes
3. Django automatically reloads
4. Refresh browser to see changes
5. No container rebuild needed!

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Credits

- Development environment powered by [Wagtail Bakerydemo](https://github.com/wagtail/bakerydemo)
- Built for the [Wagtail CMS](https://wagtail.org/) ecosystem
