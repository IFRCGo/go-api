from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from .models import InformalUpdate, InformalEmailSubscriptions, Donors
from notifications.notification import send_notification
from informal_update.serializers import InformalUpdateSerializer
from main.frontend import get_project_url
from .utils import render_to_pdf, generate_file_data


@receiver(post_save, sender=InformalUpdate)
def send_email_when_informal_update_created(sender, instance, created, **kwargs):
    if created:
        informal_update = InformalUpdateSerializer(instance)
        data = informal_update.data
        map_list = []
        graphics_list = []
        generate_file_data(data['map'], map_list)
        generate_file_data(data['graphics'], graphics_list)
        email_context = {
            'resource_url': get_project_url(instance.id),
            'title': data['title'],
            'situational_overview': data['situational_overview'],
            'map_list': map_list,
            'graphic_list': graphics_list,
            'actions_taken': data['actions_taken'],
            'resources': data['references'],
        }
        share_with_group = instance.share_with
        if share_with_group:
            if not share_with_group == InformalUpdate.InformalShareWith.RCRC_NETWORK_AND_DONOR:
                email_subscription = InformalEmailSubscriptions.objects.get(
                    share_with=str(share_with_group)
                )
                group = email_subscription.group
                if group:
                    users = User.objects.filter(groups=group)
                    users_emails = list(users.values_list('email', flat=True))
                    send_notification(
                        'Informal Update',
                        users_emails,
                        render_to_string('email/informal_update/informal_update.html', email_context),
                        'Informal Update'
                    )
            else:
                rcrc_users_email = list(
                    User.objects.filter(
                        groups__name=InformalUpdate.InformalShareWith.RCRC_NETWORK
                    ).values_list('email', flat=True)
                )
                donors_email = list(Donors.objects.all().values_list('email', flat=True))
                send_notification(
                    'Informal Update',
                    rcrc_users_email,
                    render_to_string('email/informal_update/informal_update.html', email_context),
                    'Informal Update'
                )
                send_notification(
                    'Informal Update',
                    donors_email,
                    render_to_string('email/informal_update/donor_email.html', email_context),
                    'Informal Update',
                    render_to_pdf('email/informal_update/informal_pdf.html', email_context)
                )
        return email_context
