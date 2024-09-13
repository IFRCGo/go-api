from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from sentry_sdk.crons import monitor

from deployments.models import Project, Statuses
from main.frontend import get_project_url
from main.sentry import SentryMonitor
from notifications.notification import send_notification

COMPLETE_STATUS_CHANGE_ALERT_DAYS = 5
PROJECT_STATUS_WILL_COMPLETE_MESSAGE = _(
    "<b>%(project_name)s</b> project end date is in <i>%(days)d</i> days (%(end_date)s)."  # noqa:E501
    " Please note that the project status will automatically change to <i>Completed</i>, when the end date passes."  # noqa:E501
    " You can update the end date to further keep the project in <i>Ongoing</i> status."
)


class Command(BaseCommand):

    help = "Update project status using start/end date"

    @monitor(monitor_slug=SentryMonitor.UPDATE_PROJECT_STATUS)
    def handle(self, *args, **options):
        now = timezone.now().date()

        for projects, new_status in [
            (Project.objects.filter(start_date__gt=now), Statuses.PLANNED),
            (Project.objects.filter(start_date__lte=now, end_date__gte=now), Statuses.ONGOING),
            (Project.objects.filter(end_date__lt=now), Statuses.COMPLETED),
        ]:
            updated_projects = projects.exclude(status=new_status)
            print(f"{str(new_status)} projects" f" Total: {projects.count()}," f" Updated: {updated_projects.count()}")
            updated_projects.update(status=new_status)

        # Send alert if project status will change in COMPLETE_STATUS_CHANGE_ALERT_DAYS.
        coming_end_date = now + relativedelta(days=COMPLETE_STATUS_CHANGE_ALERT_DAYS)
        notify_projects = Project.objects.filter(end_date=coming_end_date).exclude(
            # Can't send email to user without email
            Q(user__email__isnull=True)
            | Q(user__email="")
        )
        for project in notify_projects.distinct():
            user = project.user
            subject = gettext("3W Project Notification")
            admin_uri = f"admin:{Project._meta.app_label}_{Project._meta.model_name}_change"
            records = [
                {
                    "title": gettext("1 new 3W project notification"),
                    "is_staff": user.is_staff,
                    "resource_uri": get_project_url(project.id),
                    "admin_uri": reverse(admin_uri, args=(project.id,)),
                    "content": PROJECT_STATUS_WILL_COMPLETE_MESSAGE
                    % {
                        "project_name": project.name,
                        "days": COMPLETE_STATUS_CHANGE_ALERT_DAYS,
                        "end_date": coming_end_date,
                    },
                }
            ]
            send_notification(
                subject,
                [user.email],
                render_to_string(
                    "design/generic_notification.html",
                    {
                        "records": records,
                        "hide_preferences": True,
                    },
                ),
                f"Project will change to {str(Statuses.COMPLETED)} notifications - {subject}",
            )
        print(f"Notified users for {notify_projects.count()} projects for coming {str(Statuses.COMPLETED)} status")
