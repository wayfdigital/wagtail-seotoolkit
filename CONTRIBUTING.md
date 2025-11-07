# Contributing to Wagtail SEO Toolkit

Thank you for your interest in contributing to Wagtail SEO Toolkit! This document explains how to contribute to both the core (MIT) and pro (Proprietary) features.

## Dual License Structure

This project uses dual licensing:

- **Core Features** (MIT License): Free and open source
- **Pro Features** (WAYF Proprietary License): Source-available but restricted

## How to Contribute

### Core Features (MIT) - Open Contributions

Core features are **open to community contributions**. You can:

- ✅ Report bugs and issues
- ✅ Suggest new SEO checks or improvements
- ✅ Submit pull requests for bug fixes
- ✅ Add new audit checkers
- ✅ Improve documentation
- ✅ Enhance performance

**Core features include:**
- SEO audit engine (`src/wagtail_seotoolkit/core/`)
- All checkers (title, meta, content, headers, images, schema, mobile, links, freshness)
- Management commands
- Dashboard and reporting views (read-only)
- Side panels

### Pro Features (Proprietary) - Restricted Contributions

Pro features require **explicit approval from WAYF** before contributing:

- ⚠️ Contact us at hello@wayfdigital.com before working on pro features
- ⚠️ Contributions must be approved before submission
- ⚠️ You grant WAYF a license to use your contributions

**Pro features include:**
- Bulk metadata editor (`src/wagtail_seotoolkit/pro/`)
- SEO templates
- Middleware
- Subscription management
- Advanced placeholder system

## Developer Certificate of Origin (DCO)

By contributing to this project, you agree to the Developer Certificate of Origin (DCO).

### What is DCO?

The DCO is a lightweight way for contributors to certify that they have the right to contribute code. It's the same mechanism used by the Linux kernel and many other projects.

### How to Sign Off Your Commits

Add a `Signed-off-by` line to your commit messages:

```bash
git commit -s -m "Your commit message"
```

The `-s` flag automatically adds the sign-off line using your Git name and email:

```
Signed-off-by: Your Name <your.email@example.com>
```

### DCO Text

By signing off, you certify that:

(a) The contribution was created in whole or in part by you and you have the right to submit it under the license indicated in the file; or

(b) The contribution is based upon previous work that, to the best of your knowledge, is covered under an appropriate license and you have the right under that license to submit that work with modifications, whether created in whole or in part by you, under the same license (unless you are permitted to submit under a different license); or

(c) The contribution was provided directly to you by some other person who certified (a), (b) or (c) and you have not modified it.

(d) You understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information you submit with it, including your sign-off) is maintained indefinitely and may be redistributed consistent with this project or the license(s) involved.

## Contribution Process

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/wagtail-seotoolkit.git
cd wagtail-seotoolkit
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

- Follow the existing code style
- Add tests if applicable
- Update documentation
- Ensure your code works with the test project

### 4. Test Your Changes

```bash
# Run the test project
docker-compose up

# Run tests (if available)
python manage.py test
```

### 5. Commit with Sign-Off

```bash
git add .
git commit -s -m "Add your feature description"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

## Testing

- Test your changes with the included test project (bakerydemo)
- Ensure no regressions in existing functionality
- Test on supported Python versions (3.8+) and Wagtail versions (6.4+)

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions and classes
- Update relevant documentation files

## Questions?

- **General questions:** Open a [GitHub Discussion](https://github.com/wayfdigital/wagtail-seotoolkit/discussions)
- **Bugs:** Open a [GitHub Issue](https://github.com/wayfdigital/wagtail-seotoolkit/issues)
- **Pro feature contributions:** Email hello@wayfdigital.com
- **Security issues:** Email hello@wayfdigital.com (do not open public issues)

## License Grant

By contributing to this project:

- **Core features:** Your contributions will be licensed under the MIT License
- **Pro features:** You grant WAYF a perpetual, worldwide, non-exclusive, royalty-free license to use, modify, sublicense, and distribute your contributions
- You represent that you have the right to grant these licenses

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy towards other community members

---

Thank you for contributing to Wagtail SEO Toolkit! 🎉

**WAYF Digital**  
hello@wayfdigital.com  
https://wayfdigital.com

