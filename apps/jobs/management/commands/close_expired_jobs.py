from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.jobs.models import Job


class Command(BaseCommand):
    help = 'Auto-close jobs that have passed their deadline.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        expired = Job.objects.filter(
            status=Job.Status.ACTIVE,
            deadline__lt=today,
        )
        count = expired.count()
        expired.update(status=Job.Status.CLOSED)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully closed {count} expired job(s).')
        )
