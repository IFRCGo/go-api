from django.conf import settings
from django.db import models

class Pending(models.Model):
    """ Pending users requiring admin approval """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, editable=False)

    admin_contact_1 = models.EmailField(blank=True, null=True)
    admin_contact_2 = models.EmailField(blank=True, null=True)
    admin_token = models.CharField(max_length=32, null=True, editable=False)

    email_verified = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = 'Pending user'
        verbose_name_plural = 'Pending users'

    def __str__(self):
        return self.user.email


class Recovery(models.Model):
    """ Password reovery"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, editable=False)

    def __str__(self):
        return self.user.username
