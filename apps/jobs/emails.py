from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_application_received_email(application):
    """Notify job seeker that their application was received."""
    subject = f"Application Received — {application.job.title}"
    message = f"""
Hi {application.applicant.get_full_name()},

Your application for "{application.job.title}" at {application.job.company_name} has been received successfully.

We'll keep you updated on your application status.

Job Portal Team
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[application.applicant.email],
        fail_silently=True,
    )


def send_application_status_email(application):
    """Notify job seeker when their application status changes."""
    status_messages = {
        'reviewing':   'is currently being reviewed',
        'shortlisted': 'has been shortlisted! 🎉',
        'rejected':    'was not selected for this position',
        'hired':       'has been accepted — congratulations! 🎊',
    }

    status_text = status_messages.get(application.status, f'has been updated to: {application.status}')

    subject = f"Application Update — {application.job.title}"
    message = f"""
Hi {application.applicant.get_full_name()},

Your application for "{application.job.title}" at {application.job.company_name} {status_text}.

Log in to your account to view full details.

Job Portal Team
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[application.applicant.email],
        fail_silently=True,
    )


def send_new_application_email_to_employer(application):
    """Notify employer when someone applies to their job."""
    subject = f"New Application — {application.job.title}"
    message = f"""
Hi {application.job.employer.get_full_name()},

{application.applicant.get_full_name()} has applied for "{application.job.title}".

Log in to your employer dashboard to review the application.

Job Portal Team
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[application.job.employer.email],
        fail_silently=True,
    )
