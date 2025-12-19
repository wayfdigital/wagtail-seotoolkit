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
            "--skip-redirects",
            action="store_true",
            help="Skip redirect audit and chain flattening",
        )
        parser.add_argument(
            "--skip-external-check",
            action="store_true",
            help="Skip checking external redirect URLs (faster audit)",
        )
        parser.add_argument(
            "--skip-broken-links",
            action="store_true",
            help="Skip broken link audit (checking page content for broken links)",
        )
        parser.add_argument(
            "--skip-external-links",
            action="store_true",
            help="Skip checking external links in page content (faster audit)",
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

            # Run redirect audit (unless skipped)
            skip_redirects = options.get("skip_redirects", False)
            skip_external_check = options.get("skip_external_check", False)

            if not skip_redirects:
                self.run_redirect_audit(
                    audit_run,
                    debug=debug,
                    check_external=not skip_external_check,
                )

            # Run broken link audit (unless skipped)
            skip_broken_links = options.get("skip_broken_links", False)
            skip_external_links = options.get("skip_external_links", False)

            if not skip_broken_links:
                self.run_broken_link_audit(
                    audit_run,
                    debug=debug,
                    check_external=not skip_external_links,
                )

            # Generate historical report if interval condition is met
            self.generate_report_if_needed(audit_run)

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

    def generate_report_if_needed(self, audit_run):
        """Generate historical report if the configured interval has been met."""
        from django.conf import settings

        from wagtail_seotoolkit.core.utils.reporting import (
            check_email_configured,
            create_report_record,
            generate_report_data,
            send_report_email,
            should_generate_report,
        )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("CHECKING HISTORICAL REPORT GENERATION")
        self.stdout.write("=" * 60)

        # Check if we should generate a report
        should_generate, previous_audit = should_generate_report(audit_run)

        if not should_generate:
            self.stdout.write(
                "No report generated (interval not met or no previous audit)"
            )
            self.stdout.write("=" * 60)
            return

        self.stdout.write(
            f"Generating report comparing with audit from {previous_audit.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

        try:
            # Generate report data
            report_data = generate_report_data(previous_audit, audit_run)

            # Create report record
            report = create_report_record(audit_run, previous_audit, report_data)

            # Display report summary
            score_change_indicator = ""
            if report.score_change > 0:
                score_change_indicator = f"📈 +{report.score_change}"
                self.stdout.write(
                    self.style.SUCCESS(f"Score change: {score_change_indicator}")
                )
            elif report.score_change < 0:
                score_change_indicator = f"📉 {report.score_change}"
                self.stdout.write(
                    self.style.ERROR(f"Score change: {score_change_indicator}")
                )
            else:
                score_change_indicator = "➡️  No change"
                self.stdout.write(f"Score change: {score_change_indicator}")

            self.stdout.write(f"Fixed issues: {report.fixed_issues_count}")
            self.stdout.write(f"New issues: {report.new_issues_count}")
            self.stdout.write(
                f"  - On existing pages: {report.new_issues_old_pages_count}"
            )
            self.stdout.write(f"  - On new pages: {report.new_issues_new_pages_count}")

            # Check if email notification should be sent
            recipients = getattr(
                settings, "WAGTAIL_SEOTOOLKIT_REPORT_EMAIL_RECIPIENTS", []
            )

            if recipients:
                self.stdout.write(
                    f"\nSending email notification to {len(recipients)} recipient(s)..."
                )

                if check_email_configured():
                    # Send email
                    email_sent = send_report_email(report, recipients, report_data)

                    if email_sent:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "✅ Email notification sent successfully"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("⚠️  Failed to send email notification")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠️  Email not configured. Skipping email notification.\n"
                            "   Configure EMAIL_HOST and EMAIL_BACKEND in settings to enable emails."
                        )
                    )
            else:
                self.stdout.write(
                    "\nNo email recipients configured (WAGTAIL_SEOTOOLKIT_REPORT_EMAIL_RECIPIENTS)"
                )

            self.stdout.write(
                self.style.SUCCESS("\n✅ Report generated and saved to database")
            )
            self.stdout.write("=" * 60)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating report: {str(e)}"))
            self.stdout.write("=" * 60)

    def run_redirect_audit(self, audit_run, debug=False, check_external=True):
        """Run redirect audit and flatten chains."""
        import logging

        from wagtail_seotoolkit.pro.models import RedirectAuditResult
        from wagtail_seotoolkit.pro.utils.redirect_audit import audit_redirects
        from wagtail_seotoolkit.pro.utils.redirect_utils import (
            flatten_all_redirect_chains,
        )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("REDIRECT AUDIT")
        self.stdout.write("=" * 60)

        # Configure logging to output to console when debug is enabled
        redirect_audit_logger = logging.getLogger(
            "wagtail_seotoolkit.pro.utils.redirect_audit"
        )
        handler = None
        if debug:
            handler = logging.StreamHandler(self.stdout)
            handler.setFormatter(logging.Formatter("  [%(levelname)s] %(message)s"))
            redirect_audit_logger.addHandler(handler)
            redirect_audit_logger.setLevel(logging.DEBUG)

        try:
            # Run the audit
            if debug:
                self.stdout.write("Running redirect audit...")
                if not check_external:
                    self.stdout.write(
                        self.style.WARNING("  Skipping external URL checks")
                    )
                else:
                    self.stdout.write("  External URL checks: enabled")

            audit_results = audit_redirects(
                check_external=check_external,
            )

            # Display results
            total = audit_results["total_redirects"]
            chains = len(audit_results["chains"])
            loops = len(audit_results["loops"])
            to_404 = len(audit_results["redirects_to_404"])
            to_unpublished = len(audit_results["redirects_to_unpublished"])
            external = audit_results["external_redirects"]

            self.stdout.write(f"Total redirects: {total}")

            if chains > 0:
                self.stdout.write(
                    self.style.WARNING(f"  Redirect chains (>1 hop): {chains}")
                )
                if debug:
                    for chain in audit_results["chains"][:5]:  # Show first 5
                        path_str = " → ".join(chain["chain_path"])
                        self.stdout.write(f"    Chain: {path_str}")
            else:
                self.stdout.write(self.style.SUCCESS("  Redirect chains: 0"))

            if loops > 0:
                self.stdout.write(self.style.ERROR(f"  Circular loops: {loops}"))
                if debug:
                    for loop in audit_results["loops"][:5]:  # Show first 5
                        path_str = " → ".join(loop["loop_path"])
                        self.stdout.write(f"    Loop: {path_str}")
            else:
                self.stdout.write(self.style.SUCCESS("  Circular loops: 0"))

            if to_404 > 0:
                self.stdout.write(self.style.ERROR(f"  Redirects to 404: {to_404}"))
                if debug:
                    for r404 in audit_results["redirects_to_404"][:5]:
                        self.stdout.write(
                            f"    {r404['old_path']} → {r404['target']} ({r404['reason']})"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("  Redirects to 404: 0"))

            if to_unpublished > 0:
                self.stdout.write(
                    self.style.WARNING(f"  Redirects to unpublished: {to_unpublished}")
                )
            else:
                self.stdout.write(self.style.SUCCESS("  Redirects to unpublished: 0"))

            self.stdout.write(f"  External redirects: {external}")

            # Flatten chains
            self.stdout.write("\nFlattening redirect chains...")
            chains_flattened = flatten_all_redirect_chains()

            if chains_flattened > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Flattened {chains_flattened} redirect chain(s)"
                    )
                )
            else:
                self.stdout.write("No chains to flatten")

            # Store results
            RedirectAuditResult.objects.create(
                audit_run=audit_run,
                total_redirects=total,
                chains_detected=chains,
                circular_loops=loops,
                redirects_to_404=to_404,
                redirects_to_unpublished=to_unpublished,
                external_redirects=external,
                chains_flattened=chains_flattened,
                audit_details={
                    "chains": audit_results["chains"],
                    "loops": audit_results["loops"],
                    "redirects_to_404": audit_results["redirects_to_404"],
                    "redirects_to_unpublished": audit_results[
                        "redirects_to_unpublished"
                    ],
                    "statistics": audit_results["statistics"],
                },
            )

            self.stdout.write(self.style.SUCCESS("\n✅ Redirect audit completed"))
            self.stdout.write("=" * 60)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during redirect audit: {str(e)}")
            )
            if debug:
                import traceback

                self.stdout.write(traceback.format_exc())
            self.stdout.write("=" * 60)

        finally:
            # Clean up the logging handler
            if handler:
                redirect_audit_logger.removeHandler(handler)
                handler.close()

    def run_broken_link_audit(self, audit_run, debug=False, check_external=False):
        """Run broken link audit on page content."""
        import logging

        from wagtail_seotoolkit.pro.models import BrokenLinkAuditResult
        from wagtail_seotoolkit.pro.utils.broken_link_audit import audit_broken_links

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("BROKEN LINK AUDIT")
        self.stdout.write("=" * 60)

        # Configure logging to output to console when debug is enabled
        broken_link_logger = logging.getLogger(
            "wagtail_seotoolkit.pro.utils.broken_link_audit"
        )
        handler = None
        if debug:
            handler = logging.StreamHandler(self.stdout)
            handler.setFormatter(logging.Formatter("  [%(levelname)s] %(message)s"))
            broken_link_logger.addHandler(handler)
            broken_link_logger.setLevel(logging.DEBUG)

        try:
            if debug:
                self.stdout.write("Scanning pages for broken links...")
                if check_external:
                    self.stdout.write(
                        self.style.WARNING(
                            "  External link checks: enabled (this may be slow)"
                        )
                    )
                else:
                    self.stdout.write("  External link checks: disabled")

            audit_results = audit_broken_links(check_external=check_external)

            # Display results
            pages_scanned = audit_results["total_pages_scanned"]
            links_checked = audit_results["total_links_checked"]
            broken_internal = len(audit_results["broken_internal_links"])
            to_unpublished = len(audit_results["links_to_unpublished"])
            broken_external = len(audit_results["broken_external_links"])

            self.stdout.write(f"Pages scanned: {pages_scanned}")
            self.stdout.write(f"Links checked: {links_checked}")

            if broken_internal > 0:
                self.stdout.write(
                    self.style.ERROR(f"  Broken internal links: {broken_internal}")
                )
                if debug:
                    for link in audit_results["broken_internal_links"][:5]:
                        self.stdout.write(
                            f"    {link['source_page_title']}: {link['target_title']} ({link['reason']})"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("  Broken internal links: 0"))

            if to_unpublished > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Links to unpublished pages: {to_unpublished}"
                    )
                )
                if debug:
                    for link in audit_results["links_to_unpublished"][:5]:
                        self.stdout.write(
                            f"    {link['source_page_title']}: {link['target_title']}"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("  Links to unpublished pages: 0"))

            if check_external:
                if broken_external > 0:
                    self.stdout.write(
                        self.style.ERROR(f"  Broken external links: {broken_external}")
                    )
                    if debug:
                        for link in audit_results["broken_external_links"][:5]:
                            self.stdout.write(
                                f"    {link['source_page_title']}: {link['target_url']}"
                            )
                else:
                    self.stdout.write(self.style.SUCCESS("  Broken external links: 0"))

            # Store results
            BrokenLinkAuditResult.objects.create(
                audit_run=audit_run,
                total_pages_scanned=pages_scanned,
                total_links_checked=links_checked,
                broken_internal_links=broken_internal,
                links_to_unpublished=to_unpublished,
                broken_external_links=broken_external,
                audit_details={
                    "broken_internal_links": audit_results["broken_internal_links"],
                    "links_to_unpublished": audit_results["links_to_unpublished"],
                    "broken_external_links": audit_results["broken_external_links"],
                },
            )

            self.stdout.write(self.style.SUCCESS("\n✅ Broken link audit completed"))
            self.stdout.write("=" * 60)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during broken link audit: {str(e)}")
            )
            if debug:
                import traceback

                self.stdout.write(traceback.format_exc())
            self.stdout.write("=" * 60)

        finally:
            # Clean up the logging handler
            if handler:
                broken_link_logger.removeHandler(handler)
                handler.close()
