from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Page

from wagtail_seotoolkit.models import SEOAuditRun
from wagtail_seotoolkit.utils.seo_audit import run_audit_on_pages


class Command(BaseCommand):
    help = "Run a SEO audit on the site"

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=None,
            help='Limit the number of pages to audit (default: all pages)'
        )
        parser.add_argument(
            '--page-id',
            type=int,
            default=None,
            help='Audit a specific page by ID'
        )
        parser.add_argument(
            '--no-progress',
            action='store_true',
            help='Disable progress bar'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting SEO audit...'))
        
        # Create audit run
        audit_run = SEOAuditRun.objects.create(
            overall_score=0,
            pages_analyzed=0,
            status='running'
        )
        
        try:
            # Get pages to audit
            pages = self.get_pages_to_audit(options)
            total_pages = len(pages)
            
            self.stdout.write(f"Found {total_pages} page(s) to audit\n")

            # Run the audit
            show_progress = not options.get('no_progress', False)
            results = run_audit_on_pages(
                pages,
                audit_run,
                show_progress=show_progress,
            )
            
            # Display summary
            self.display_summary(results)
            
        except Exception as e:
            audit_run.status = 'failed'
            audit_run.save()
            raise CommandError(f'Audit failed: {str(e)}')
    
    def get_pages_to_audit(self, options):
        """Get the list of pages to audit based on command options."""
        if options['page_id']:
            # Audit specific page
            try:
                page = Page.objects.get(id=options['page_id']).specific
                return [page]
            except Page.DoesNotExist:
                raise CommandError(f"Page with ID {options['page_id']} not found")
        
        # Get all live pages
        pages = Page.objects.live().public().specific()
        
        # Exclude root and system pages
        pages = pages.exclude(depth__lte=2)
        
        # Limit if specified
        if options['pages']:
            pages = pages[:options['pages']]
        
        return list(pages)
    
    def display_summary(self, results):
        """Display audit results summary."""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SEO AUDIT COMPLETED'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"Pages analyzed: {results['total_pages']}")
        self.stdout.write(f"Total issues found: {results['total_issues']}")
        self.stdout.write(f"Overall score: {results['overall_score']}/100")
        
        # Break down by severity
        self.stdout.write(self.style.ERROR(f"  High severity: {results['high_issues']}"))
        self.stdout.write(self.style.WARNING(f"  Medium severity: {results['medium_issues']}"))
        self.stdout.write(f"  Low severity: {results['low_issues']}")
        self.stdout.write(self.style.SUCCESS('='*60))
