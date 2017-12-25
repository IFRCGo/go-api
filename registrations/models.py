from django.db import models

class Pending(models.Model):
    """ Pending users requiring admin approval """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=12, editable=False)

    admin_contact_1 = models.EmailField(blank=True, null=True)
    admin_contact_2 = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.user.email
