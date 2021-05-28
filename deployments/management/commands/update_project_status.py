from django.core.management.base import BaseCommand
from django.utils import timezone

from deployments.models import Project, Statuses


class Command(BaseCommand):
    help = 'Update project status using start/end date'

    def handle(self, *args, **options):
        now = timezone.now().date()

        for projects, new_status in [
                (Project.objects.filter(start_date__gt=now), Statuses.PLANNED),
                (Project.objects.filter(start_date__lte=now, end_date__gte=now), Statuses.ONGOING),
                (Project.objects.filter(end_date__lt=now), Statuses.COMPLETED),
        ]:
            print(f'Total {str(new_status)} projects: {projects.count()}')
            projects.update(status=new_status)
