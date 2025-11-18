import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef
from django.utils import timezone


def parse_interval(interval_str):
    """
    Parse interval string like "7d", "2w", "1m" into a timedelta.

    Args:
        interval_str: String in format like "7d" (days), "2w" (weeks), "1m" (months)

    Returns:
        timedelta object representing the interval

    Raises:
        ValueError: If the interval string is invalid
    """
    match = re.match(r"^(\d+)([dwm])$", interval_str.lower())
    if not match:
        raise ValueError(
            f"Invalid interval format: {interval_str}. "
            "Expected format: number followed by d (days), w (weeks), or m (months). "
            "Examples: '7d', '2w', '1m'"
        )

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    elif unit == "m":
        # Approximate month as 30 days
        return timedelta(days=value * 30)

    raise ValueError(f"Unsupported time unit: {unit}")


def should_generate_report(current_audit):
    """
    Check if a report should be generated based on the configured interval.

    Args:
        current_audit: The current SEOAuditRun instance

    Returns:
        tuple: (should_generate: bool, previous_audit: SEOAuditRun or None)
    """
    from wagtail_seotoolkit.core.models import SEOAuditReport, SEOAuditRun

    # Get the interval setting
    interval_str = getattr(settings, "WAGTAIL_SEOTOOLKIT_REPORT_INTERVAL", "7d")

    try:
        interval = parse_interval(interval_str)
    except ValueError as e:
        print(f"Warning: {e}. Using default interval of 7 days.")
        interval = timedelta(days=7)

    # Get the latest report
    latest_report = SEOAuditReport.objects.order_by("-created_at").first()

    if not latest_report:
        # No previous reports, generate first report comparing with the audit at least interval ago
        previous_audit = (
            SEOAuditRun.objects.filter(
                status="completed", created_at__lte=current_audit.created_at - interval
            )
            .order_by("-created_at")
            .first()
        )
        return (previous_audit is not None, previous_audit)

    # Check if enough time has passed since the last report
    time_since_last_report = current_audit.created_at - latest_report.created_at

    if time_since_last_report >= interval:
        # Compare against the audit that was used in the last report
        # (the current_audit of the last report is where we left off)
        previous_audit = latest_report.current_audit

        # Verify it's still a valid comparison (the audit still exists and is completed)
        if previous_audit.status == "completed":
            return (True, previous_audit)

        # Fallback: if the previous audit is invalid, try to find another one
        previous_audit = (
            SEOAuditRun.objects.filter(
                status="completed",
                created_at__lte=current_audit.created_at - interval,
            )
            .order_by("-created_at")
            .first()
        )

        return (previous_audit is not None, previous_audit)

    return (False, None)


def generate_report_data(prev_audit, new_audit):
    """
    Calculate all metrics for a report comparing two audits.

    Args:
        prev_audit: The previous SEOAuditRun
        new_audit: The current SEOAuditRun

    Returns:
        dict: Dictionary containing all report metrics
    """
    # Calculate score change
    score_change = new_audit.overall_score - prev_audit.overall_score

    # Get issue counts using existing helper functions
    all_new_issues = get_all_new_issues(prev_audit, new_audit)
    all_fixed_issues = get_all_fixed_issues(prev_audit, new_audit)
    new_issues_old_pages = get_new_issues_for_old_pages(prev_audit, new_audit)
    new_issues_new_pages = get_new_issues_for_new_pages(prev_audit, new_audit)

    return {
        "score_change": score_change,
        "new_issues_count": all_new_issues.count(),
        "fixed_issues_count": all_fixed_issues.count(),
        "new_issues_old_pages_count": new_issues_old_pages.count(),
        "new_issues_new_pages_count": new_issues_new_pages.count(),
        "all_new_issues": all_new_issues,
        "all_fixed_issues": all_fixed_issues,
        "new_issues_old_pages": new_issues_old_pages,
        "new_issues_new_pages": new_issues_new_pages,
    }


def create_report_record(current_audit, previous_audit, data):
    """
    Save a SEOAuditReport record to the database.

    Args:
        current_audit: The current SEOAuditRun
        previous_audit: The previous SEOAuditRun
        data: Dictionary containing report metrics from generate_report_data

    Returns:
        SEOAuditReport: The created report instance
    """
    from wagtail_seotoolkit.core.models import SEOAuditReport

    report = SEOAuditReport.objects.create(
        current_audit=current_audit,
        previous_audit=previous_audit,
        score_change=data["score_change"],
        new_issues_count=data["new_issues_count"],
        fixed_issues_count=data["fixed_issues_count"],
        new_issues_old_pages_count=data["new_issues_old_pages_count"],
        new_issues_new_pages_count=data["new_issues_new_pages_count"],
    )

    return report


def check_email_configured():
    """
    Check if Django email settings are configured.

    Returns:
        bool: True if email is configured, False otherwise
    """
    # Check if EMAIL_HOST is configured
    email_host = getattr(settings, "EMAIL_HOST", None)

    if not email_host or email_host == "":
        return False

    # Additional check: EMAIL_BACKEND should be set
    email_backend = getattr(settings, "EMAIL_BACKEND", "")

    # Console backend is not considered "configured" for production use
    if "console" in email_backend.lower() and not settings.DEBUG:
        return False

    return True if not settings.DEBUG else True


def format_report_email(report, detailed_data):
    """
    Generate HTML email body for a report using Django template.

    Args:
        report: SEOAuditReport instance
        detailed_data: Dictionary with detailed issue querysets from generate_report_data

    Returns:
        str: HTML email body
    """
    from django.template.loader import render_to_string

    # Score change indicator
    if report.score_change > 0:
        score_indicator = f"📈 +{report.score_change}"
        score_class = "positive"
    elif report.score_change < 0:
        score_indicator = f"📉 {report.score_change}"
        score_class = "negative"
    else:
        score_indicator = "➡️ No change"
        score_class = "neutral"

    # Get new issues (expanded to 20)
    new_issues = detailed_data["all_new_issues"].order_by(
        "-issue_severity", "issue_type"
    )[:20]

    # Render template
    context = {
        "report": report,
        "score_indicator": score_indicator,
        "score_class": score_class,
        "new_issues": new_issues,
    }

    html_body = render_to_string("wagtail_seotoolkit/emails/audit_report.html", context)

    return html_body


def send_report_email(report, recipients, detailed_data):
    """
    Send email notification for a report.

    Args:
        report: SEOAuditReport instance
        recipients: List of email addresses
        detailed_data: Dictionary with detailed issue querysets from generate_report_data

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not recipients:
        return False

    if not check_email_configured():
        print("Warning: Email is not configured. Skipping email notification.")
        return False

    try:
        html_body = format_report_email(report, detailed_data)

        # Determine subject based on score change
        if report.score_change > 0:
            subject = f"✅ SEO Score Improved: +{report.score_change} points"
        elif report.score_change < 0:
            subject = f"⚠️ SEO Score Declined: {report.score_change} points"
        else:
            subject = "📊 SEO Audit Report - No Score Change"

        send_mail(
            subject=subject,
            message="",  # Empty plain text, HTML is the primary content
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=recipients,
            html_message=html_body,
            fail_silently=False,
        )

        # Update report to mark email as sent
        report.email_sent = True
        report.email_sent_at = timezone.now()
        report.save()

        return True

    except Exception as e:
        print(f"Error sending report email: {e}")
        return False


def get_all_new_issues(prev_audit, new_audit):
    """
    Get all issues in new_audit that don't exist in prev_audit
    (based on matching page and issue_type).
    """
    # Subquery to check if an issue with same page and issue_type exists in prev_audit
    prev_issues_subquery = prev_audit.issues.filter(
        page=OuterRef("page"), issue_type=OuterRef("issue_type")
    )

    # Return issues from new_audit that don't exist in prev_audit
    return new_audit.issues.exclude(Exists(prev_issues_subquery))


def get_all_fixed_issues(prev_audit, new_audit):
    """
    Get all issues in prev_audit that don't exist in new_audit
    (based on matching page and issue_type).
    """
    # Subquery to check if an issue with same page and issue_type exists in new_audit
    new_issues_subquery = new_audit.issues.filter(
        page=OuterRef("page"), issue_type=OuterRef("issue_type")
    )
    return prev_audit.issues.exclude(Exists(new_issues_subquery))


def get_new_issues_for_old_pages(prev_audit, new_audit):
    new_issues = get_all_new_issues(prev_audit, new_audit)
    return new_issues.filter(page__first_published_at__lte=prev_audit.created_at)


def get_new_issues_for_new_pages(prev_audit, new_audit):
    new_issues = get_all_new_issues(prev_audit, new_audit)
    return new_issues.filter(page__first_published_at__gt=prev_audit.created_at)
