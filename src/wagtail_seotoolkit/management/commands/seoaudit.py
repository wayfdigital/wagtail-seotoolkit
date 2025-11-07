from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Page

from wagtail_seotoolkit.core.models import SEOAuditRun
from wagtail_seotoolkit.core.utils.seo_audit import execute_audit_run


class Command(BaseCommand):
    help = "Run a SEO audit on the site"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=None,
            help="Limit the number of pages to audit (default: all pages)",
        )
        parser.add_argument(
            "--page-id", type=int, default=None, help="Audit a specific page by ID"
        )
        parser.add_argument(
            "--no-progress", action="store_true", help="Disable progress bar"
        )
        parser.add_argument(
            "--skip-pagespeed",
            action="store_true",
            help="Skip PageSpeed Insights checks",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug output showing API calls and responses",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Use mock PageSpeed data instead of real API calls",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting SEO audit..."))

        # Handle dry-run mode by updating settings temporarily
        if options.get("dry_run"):
            from django.conf import settings

            settings.WAGTAIL_SEOTOOLKIT_PAGESPEED_DRY_RUN = True
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE: Using mock PageSpeed data")
            )

        # Safety mechanism: Mark all other running audits as failed
        running_audits = SEOAuditRun.objects.filter(status="running")
        if running_audits.exists():
            count = running_audits.count()
            running_audits.update(status="failed")
            self.stdout.write(
                self.style.WARNING(
                    f"SAFETY: Marked {count} previously running audit(s) as failed"
                )
            )

        # Create audit run
        audit_run = SEOAuditRun.objects.create(
            overall_score=0, pages_analyzed=0, status="running"
        )

        try:
            # Get pages to audit
            pages = self.get_pages_to_audit(options)
            total_pages = len(pages)

            self.stdout.write(f"Found {total_pages} page(s) to audit\n")

            # Run the audit using the new reusable function
            show_progress = not options.get("no_progress", False)
            debug = options.get("debug", False)
            skip_pagespeed = options.get("skip_pagespeed", False)

            if debug:
                self.stdout.write(
                    self.style.WARNING("DEBUG MODE: Showing API calls and responses")
                )

            if skip_pagespeed:
                self.stdout.write(self.style.WARNING("SKIPPING PageSpeed checks"))

            results = execute_audit_run(
                audit_run,
                pages=pages,
                show_progress=show_progress,
                debug=debug,
                skip_pagespeed=skip_pagespeed,
            )

            # Display summary
            self.display_summary(results)

        except KeyboardInterrupt:
            # Handle user cancellation (Ctrl+C)
            audit_run.status = "failed"
            audit_run.save()
            self.stdout.write(self.style.ERROR("\n\nAudit cancelled by user (Ctrl+C)"))
            self.stdout.write(self.style.ERROR("Audit marked as failed."))
            raise CommandError("Audit cancelled by user")

        except Exception as e:
            audit_run.status = "failed"
            audit_run.save()
            raise CommandError(f"Audit failed: {str(e)}")

    def get_pages_to_audit(self, options):
        """Get the list of pages to audit based on command options."""
        if options["page_id"]:
            # Audit specific page
            try:
                page = Page.objects.get(id=options["page_id"]).specific
                return [page]
            except Page.DoesNotExist:
                raise CommandError(f"Page with ID {options['page_id']} not found")

        # Get all live pages
        pages = Page.objects.live().public().specific()

        # Exclude root and system pages
        pages = pages.exclude(depth__lte=2)

        # Filter out pages without site assigned
        for page in pages:
            if not page.full_url:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Skipping {page.title} because it has no site assigned"
                    )
                )
                pages = pages.exclude(id=page.id)

        # Limit if specified
        if options["pages"]:
            pages = pages[: options["pages"]]

        return list(pages)

    def display_summary(self, results):
        """Display audit results summary."""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("SEO AUDIT COMPLETED"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"Pages analyzed: {results['total_pages']}")
        self.stdout.write(f"Total issues found: {results['total_issues']}")
        self.stdout.write(f"Overall score: {results['overall_score']}/100")

        # Break down by severity
        self.stdout.write(
            self.style.ERROR(f"  High severity: {results['high_issues']}")
        )
        self.stdout.write(
            self.style.WARNING(f"  Medium severity: {results['medium_issues']}")
        )
        self.stdout.write(f"  Low severity: {results['low_issues']}")
        self.stdout.write(self.style.SUCCESS("=" * 60))

