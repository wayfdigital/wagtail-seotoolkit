# Wagtail SEO Toolkit

A comprehensive SEO toolkit for Wagtail CMS that provides essential SEO features and optimizations for your Wagtail websites.

## Compatibility

| Wagtail | Django | Python |
|---------|--------|--------|
| 7.0 LTS, 7.1+ | 4.2, 5.1, 5.2 | 3.9, 3.10, 3.11, 3.12, 3.13 |
| 6.0 - 6.4 | 4.2, 5.0, 5.1, 5.2 | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 |
| 5.2 LTS | 3.2, 4.1, 4.2, 5.0 | 3.8, 3.9, 3.10, 3.11, 3.12 |
| 5.0, 5.1 | 3.2, 4.1, 4.2 | 3.7, 3.8, 3.9, 3.10, 3.11 |

**Minimum requirements:**
- Python 3.8+
- Django 3.2+
- Wagtail 5.0+

## Current Features

- **Admin Menu Item**: Adds "SEO Toolkit" entry to Wagtail admin sidebar with cog icon
- *(Package structure ready for expansion - more features coming soon)*

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

### Development Workflow

The development environment is configured with **live code reloading**:

1. Edit package code in `src/wagtail_seotoolkit/`
2. Save your changes
3. Django automatically reloads
4. Refresh browser to see changes
5. No container rebuild needed!

**What's mounted as volumes:**
- `./src` - Your package source code
- `./testproject` - Bakerydemo test project
- Package config files (pyproject.toml, setup.py, etc.)

### Useful Docker Commands

```bash
# Start containers (foreground - see logs)
docker compose up

# Start in background
docker compose up -d

# Stop containers
docker compose down

# View logs
docker compose logs -f web

# Rebuild after dependency changes
docker compose up --build

# Run Django commands
docker compose exec web python manage.py <command>

# Access Django shell
docker compose exec web python manage.py shell

# Run tests
docker compose exec web pytest
```

### About the Test Project

The development environment uses [Wagtail Bakerydemo](https://github.com/wagtail/bakerydemo), a full-featured Wagtail site with:
- Blog pages
- Recipe pages (Breads)
- Location pages
- Gallery pages
- Forms
- Initial data with sample content

The `wagtail_seotoolkit` package is automatically installed and configured in the demo's `INSTALLED_APPS`, so you can immediately test your SEO features on real Wagtail pages.

## Installation for Production

Once published to PyPI, install via:

```bash
pip install wagtail-seotoolkit
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/yourusername/wagtail-seotoolkit.git
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ... your other apps
    'wagtail_seotoolkit',  # Add before Wagtail apps
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    # ... rest of Wagtail apps
]
```

## Extending the Package

The package structure is ready for you to add features:

- **Add views**: Create `views.py` for admin pages
- **Add URLs**: Create `urls.py` and register with `register_admin_urls` hook
- **Add models**: Extend `models.py` with SEO mixins for pages
- **Add blocks**: Extend `blocks.py` with StreamField blocks
- **Add templates**: Add to `templates/wagtail_seotoolkit/`

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

---

## Publishing to PyPI (When Ready)

### Prerequisites

Install build tools:

```bash
pip install build twine
```

### Building the Package

Create distribution packages:

```bash
python -m build
```

This creates `dist/` folder with `.whl` and `.tar.gz` files.

### Testing with TestPyPI (Recommended First)

1. **Register an account:** https://test.pypi.org/account/register/

2. **Upload to TestPyPI:**

```bash
python -m twine upload --repository testpypi dist/*
```

3. **Test installation:**

```bash
pip install --index-url https://test.pypi.org/simple/ wagtail-seotoolkit
```

### Publishing to PyPI

Once tested on TestPyPI:

1. **Register an account:** https://pypi.org/account/register/

2. **Upload to PyPI:**

```bash
python -m twine upload dist/*
```

3. **Install from PyPI:**

```bash
pip install wagtail-seotoolkit
```

### Best Practices

- **Use API tokens** (generate in PyPI account settings)
- **Bump version** in `src/wagtail_seotoolkit/__init__.py` before each release
- **Clean dist folder** between releases: `rm -rf dist/`
- **Tag releases** in git: `git tag v0.1.0 && git push --tags`

---

## Credits

- Development environment powered by [Wagtail Bakerydemo](https://github.com/wagtail/bakerydemo)
- Built for the [Wagtail CMS](https://wagtail.org/) ecosystem

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/wagtail-seotoolkit/issues)
- **Wagtail Slack**: [wagtail.org/slack](https://wagtail.org/slack/)
