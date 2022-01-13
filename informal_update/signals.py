import json

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.contrib.auth.models import Group, User

from .models import InformalUpdate
from notifications.notification import send_notification
from informal_update.serializers import InformalUpdateSerializer


@receiver(post_save, sender=InformalUpdate)
def send_email_when_informal_update_created(sender, instance, created, **kwargs):
    if created:
        share_with_group = instance.share_with
        # group, created = Group.objects.get_or_create(name=share_with_group)
        # users_emails = User.objects.filter(groups__name=group).values_list('email', flat=True)
        informal_update = InformalUpdateSerializer(instance)
        data = json.loads(json.dumps(informal_update.data))
        email_context = {
            'title': data['title'],
            'situational_overview': data['situational_overview'],
            'map': data['map_details'],
            'graphic': data['graphics_details'],
            'actions_taken': data['actions_taken'],
            'resources': data['references'],
        }
        # send_notification(
        #     'Informal Update',
        #     list(users_emails),
        #     render_to_string('email/informal_update.html', email_context),
        #     'Informal Update'
        # )
        return email_context
