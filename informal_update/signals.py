from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings

from .models import InformalUpdate, InformalEmailSubscriptions, Donors
from notifications.notification import send_notification
from informal_update.serializers import InformalUpdateSerializer
from main.frontend import get_project_url
from .utils import render_to_pdf


@receiver(post_save, sender=InformalUpdate)
def send_email_when_informal_update_created(sender, instance, created, **kwargs):
    if created:
        share_with_group = instance.share_with
        email_subscription = InformalEmailSubscriptions.objects.get(
            share_with=str(share_with_group)
        )
        group = email_subscription.group
        if group:
            users = User.objects.filter(groups=group)
            users_emails = list(users.values_list('email', flat=True))
            informal_update = InformalUpdateSerializer(instance)
            data = informal_update.data
            donors_emails = list(Donors.objects.all().values_list('email', flat=True))
            map_list = []
            for map in data['map_details']:
                maps = dict()
                if map['file']:
                    map_url = settings.BASE_URL + map['file']
                    maps['image'] = map_url
                maps['caption'] = map['caption']
                map_list.append(maps)
            graphics_list = []
            for graphic in data['graphics_details']:
                graphics = dict()
                if graphic['file']:
                    graphics_url = settings.BASE_URL + graphic['file']
                    graphics['image'] = graphics_url
                graphics['caption'] = graphic['caption']
                graphics_list.append(graphics)

            email_context = {
                'resource_url': get_project_url(instance.id),
                'title': data['title'],
                'situational_overview': data['situational_overview'],
                'map_list': map_list,
                'graphic_list': graphics_list,
                'actions_taken': data['actions_taken'],
                'resources': data['references'],
            }

            send_notification(
                'Informal Update',
                users_emails,
                render_to_string('email/informal_update.html', email_context),
                'Informal Update'
            )
            # send_notification(
            #     'Informal Update',
            #     donors_emails,
            #     render_to_pdf('email/informal_email_pdf.html', email_context),
            #     'Informal Update'
            # )
            return email_context
