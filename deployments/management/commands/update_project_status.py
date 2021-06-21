from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from notifications.notification import send_notification
from deployments.models import Project, Statuses


COMPLETE_STATUS_CHANGE_ALERT_DAYS = 5


class Command(BaseCommand):

    help = 'Update project status using start/end date'

    def handle(self, *args, **options):
        now = timezone.now().date()

        for projects, new_status in [
                (Project.objects.filter(start_date__gt=now), Statuses.PLANNED),
                (Project.objects.filter(start_date__lte=now, end_date__gte=now), Statuses.ONGOING),
                (Project.objects.filter(end_date__lt=now), Statuses.COMPLETED),
        ]:
            updated_projects = projects.exclude(status=new_status)
            print(
                f'{str(new_status)} projects'
                f' Total: {projects.count()},'
                f' Updated: {updated_projects.count()}'
            )
            updated_projects.update(status=new_status)

        # Send alert if project status will change in COMPLETE_STATUS_CHANGE_ALERT_DAYS.
        coming_end_date = now + relativedelta(days=COMPLETE_STATUS_CHANGE_ALERT_DAYS)
        notify_projects = Project.objects.filter(end_date=coming_end_date).exclude(
            # Can't send email to user without email
            Q(user__email__isnull=True) | Q(user__email='')
        )
        for project in notify_projects.distinct():
            subject = '3W Project Notification'
            send_notification(
                subject,
                [project.user.email],
                render_to_string(
                    'email/deployments/project_status_complete_pre_alert.html', {
                        'project': project,
                        'end_date': coming_end_date,
                    }
                ),
                f'Project will change to {str(Statuses.COMPLETED)} notifications - {subject}',
            )
        print(f'Notified users for {notify_projects.count()} projects for coming {str(Statuses.COMPLETED)} status')
