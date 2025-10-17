from django.core.management.base import BaseCommand, CommandError

from wagtail_seotoolkit.models import SEOAuditRun
from wagtail_seotoolkit.utils.seo_audit import execute_audit_run


class Command(BaseCommand):
    help = "Run any scheduled SEO audits"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-progress',
            action='store_true',
            help='Disable progress bar'
        )

    def handle(self, *args, **options):
        # Check if there's already a running audit
        running_audit = SEOAuditRun.objects.filter(status='running').first()
        if running_audit:
            self.stdout.write(
                self.style.WARNING(
                    f'Audit run {running_audit.id} is already running. Skipping.'
                )
            )
            return

        # Get the oldest scheduled audit
        scheduled_audit = SEOAuditRun.objects.filter(status='scheduled').order_by('created_at').first()
        
        if not scheduled_audit:
            self.stdout.write(
                self.style.SUCCESS('No scheduled audits found.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Starting scheduled audit run {scheduled_audit.id}...')
        )

        try:
            # Execute the audit
            show_progress = not options.get('no_progress', False)
            results = execute_audit_run(scheduled_audit, show_progress=show_progress)
            
            # Display summary
            self.display_summary(results)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Scheduled audit failed: {str(e)}')
            )
            raise CommandError(f'Audit failed: {str(e)}')
    
    def display_summary(self, results):
        """Display audit results summary."""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SCHEDULED SEO AUDIT COMPLETED'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"Pages analyzed: {results['total_pages']}")
        self.stdout.write(f"Total issues found: {results['total_issues']}")
        self.stdout.write(f"Overall score: {results['overall_score']}/100")
        
        # Break down by severity
        self.stdout.write(self.style.ERROR(f"  High severity: {results['high_issues']}"))
        self.stdout.write(self.style.WARNING(f"  Medium severity: {results['medium_issues']}"))
        self.stdout.write(f"  Low severity: {results['low_issues']}")
        self.stdout.write(self.style.SUCCESS('='*60))
