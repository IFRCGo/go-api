import uuid

import reversion
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Pending(models.Model):
    """Pending users requiring admin approval"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        primary_key=True,
        editable=False,
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    token = models.CharField(verbose_name=_("token"), max_length=32, editable=False)

    admin_contact_1 = models.EmailField(verbose_name=_("admin contact 1"), blank=True, null=True, editable=False)
    admin_contact_2 = models.EmailField(verbose_name=_("admin contact 2"), blank=True, null=True, editable=False)
    admin_token_1 = models.CharField(verbose_name=_("admin token 1"), max_length=32, null=True, editable=False)
    admin_token_2 = models.CharField(verbose_name=_("admin token 2"), max_length=32, null=True, editable=False)
    admin_1_validated = models.BooleanField(verbose_name=_("admin 1 validated"), default=False, editable=False)
    admin_2_validated = models.BooleanField(verbose_name=_("admin 2 validated"), default=False, editable=False)
    admin_1_validated_date = models.DateTimeField(verbose_name=_("admin 1 validated date"), null=True, blank=True, editable=False)
    admin_2_validated_date = models.DateTimeField(verbose_name=_("admin 2 validated date"), null=True, blank=True, editable=False)
    email_verified = models.BooleanField(verbose_name=_("email verified?"), default=False, editable=False)
    justification = models.CharField(verbose_name=_("justification"), max_length=500, blank=True, null=True)
    reminder_sent_to_admin = models.BooleanField(verbose_name=_("reminder sent to admin?"), default=False, editable=False)

    class Meta:
        verbose_name = _("Pending user")
        verbose_name_plural = _("Pending users")

    def __str__(self):
        return self.user.email


class Recovery(models.Model):
    """Password recovery"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    token = models.CharField(verbose_name=_("token"), max_length=32, editable=False)

    class Meta:
        verbose_name = _("Recovery")
        verbose_name_plural = _("Recoveries")

    def __str__(self):
        return self.user.username


@reversion.register()
class DomainWhitelist(models.Model):
    """Whitelisted domains"""

    domain_name = models.CharField(verbose_name=_("domain name"), max_length=200)
    description = models.TextField(verbose_name=_("description"), null=True, blank=True)
    is_active = models.BooleanField(verbose_name=_("is active?"), default=True)

    class Meta:
        verbose_name = _("Domain Whitelist")
        verbose_name_plural = _("Domains Whitelist")

    def __str__(self):
        return self.domain_name


class UserExternalToken(models.Model):
    """External token for user"""

    title = models.CharField(
        verbose_name=_("title"),
        max_length=255,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    jti = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text=_("Unique identifier for the token"))
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    expire_timestamp = models.DateTimeField(verbose_name=_("expire timestamp"))
    # @Note: Currently not used, but could be utilized for a blacklist feature.
    # is_disabled = models.BooleanField(verbose_name=_('is disabled?'), default=False)

    class Meta:
        verbose_name = _("User External Token")
        verbose_name_plural = _("User External Tokens")

    def __str__(self):
        return f'{self.title}-{self.expire_timestamp.strftime("%Y-%m-%d")}'

    def get_payload(self) -> dict:
        return {"jti": str(self.jti), "userId": self.user_id, "exp": self.expire_timestamp, "inMovement": True}
