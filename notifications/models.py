from django.db import models
from django.conf import settings


class Subscription(models.Model):
    """ User subscriptions """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    event_type = models.CharField(
        choices = (
            ('NEW', 'New record'),
            ('EDIT', 'Edit to existing record'),
        ),
        max_length=4,
    )

    record_type = models.CharField(
        choices = (
            ('EVNT', 'Disaster'),
            ('APPL', 'Appeal'),
            ('FRPT', 'Field report'),
        ),
        max_length=4,
    )
