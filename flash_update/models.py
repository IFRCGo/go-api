import reversion
from tinymce import HTMLField

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import Group

from api.models import (
    Country,
    District,
    DisasterType,
    ActionOrg,
    ActionType,
    ActionCategory,
)


@reversion.register()
class FlashGraphicMap(models.Model):
    file = models.FileField(
        verbose_name=_('file'),
        upload_to='flash_update/images/'
    )
    caption = models.CharField(max_length=225, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created_by'),
        on_delete=models.SET_NULL, null=True,
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('flash graphic map')
        verbose_name_plural = _('flash graphic maps')


@reversion.register()
class FlashReferences(models.Model):
    date = models.DateField(verbose_name=_('date'), blank=True)
    source_description = models.CharField(verbose_name=_('Name or Source Description'), max_length=225, blank=True)
    url = models.TextField(blank=True)
    document = models.ForeignKey(
        FlashGraphicMap, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('document'),
        related_name='flash_document'
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('flash reference')
        verbose_name_plural = _('flash references')

    def __str__(self):
        return f'{self.source_description} - {self.date}'


@reversion.register()
class FlashUpdate(models.Model):
    '''
    This is a base model for Flash Update
    '''

    class FlashShareWith(models.TextChoices):
        IFRC_SECRETARIAT = 'ifrc_secretariat', _('IFRC Secretariat')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created by'), related_name='flash_update_created_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('modified by'), related_name='flash_update_modified_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('updated at'), auto_now=True)

    # context
    hazard_type = models.ForeignKey(
        DisasterType, verbose_name=_('hazard type'), related_name='flash_update_hazard_type',
        null=True, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=300)
    situational_overview = HTMLField(verbose_name=_('Situational Overview'), blank=True, default='')

    # map/graphics
    map = models.ManyToManyField(
        FlashGraphicMap, blank=True,
        verbose_name=_('map'),
        related_name='flash_map'
    )
    graphics = models.ManyToManyField(
        FlashGraphicMap, blank=True,
        verbose_name=_('graphics'),
        related_name='flash_graphics'
    )

    # Focal Point
    originator_name = models.CharField(verbose_name=_('originator_name'), max_length=100, null=True, blank=True)
    originator_title = models.CharField(verbose_name=_('originator_title'), max_length=300, null=True, blank=True)
    originator_email = models.CharField(verbose_name=_('originator_email'), max_length=300, null=True, blank=True)
    originator_phone = models.CharField(verbose_name=_('originator_phone'), max_length=50, null=True, blank=True)

    ifrc_name = models.CharField(verbose_name=_('ifrc_name'), max_length=100, null=True, blank=True)
    ifrc_title = models.CharField(verbose_name=_('ifrc_title'), max_length=300, null=True, blank=True)
    ifrc_email = models.CharField(verbose_name=_('ifrc_email'), max_length=300, null=True, blank=True)
    ifrc_phone = models.CharField(verbose_name=_('ifrc_phone'), max_length=50, null=True, blank=True)

    # Share with
    share_with = models.CharField(
        max_length=50, choices=FlashShareWith.choices, default=FlashShareWith.IFRC_SECRETARIAT,
        null=True, blank=True, verbose_name=_('share with')
    )
    references = models.ManyToManyField(
        FlashReferences, blank=True,
        verbose_name=_('references')
    )
    extracted_file = models.FileField(
        verbose_name=_('extracted file'),
        upload_to='flash_update/pdf/',
        blank=True,
        null=True
    )
    extracted_at = models.DateTimeField(verbose_name=_('extracted at'), blank=True, null=True)

    class Meta:
        verbose_name = _('Flash update')
        verbose_name_plural = _('Flash updates')

    def __str__(self):
        return f'{self.title}'


@reversion.register()
class FlashCountryDistrict(models.Model):
    flash_update = models.ForeignKey(
        FlashUpdate, on_delete=models.CASCADE,
        verbose_name=_('Flash update'),
        related_name='flash_country_district'
    )
    country = models.ForeignKey(
        Country, verbose_name=_('country'), on_delete=models.CASCADE,
        related_name='flash_country'
    )
    district = models.ManyToManyField(
        District, verbose_name=_('district'),
        related_name='flash_district',
        blank=True
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('flash_update', 'country')
        verbose_name = _('flash country district')
        verbose_name_plural = _('flash countries districts')

    def __str__(self):
        return f'{self.country} - {self.district}'


@reversion.register()
class FlashAction(models.Model):
    """ Action taken for Flash Update """

    name = models.CharField(verbose_name=_('name'), max_length=400)
    organizations = ArrayField(
        models.CharField(choices=ActionOrg.choices, max_length=4),
        verbose_name=_('organizations'), default=list, blank=True
    )
    flash_update_types = ArrayField(
        models.CharField(choices=ActionType.choices, max_length=16),
        verbose_name=_('flash update types'), default=list,
    )
    category = models.CharField(
        max_length=255, verbose_name=_('category'), choices=ActionCategory.choices, default=ActionCategory.GENERAL
    )
    is_disabled = models.BooleanField(verbose_name=_('is disabled?'), default=False, help_text=_('Disable in form'))
    tooltip_text = models.TextField(verbose_name=_('tooltip text'), null=True, blank='true')
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('flash action')
        verbose_name_plural = _('flash actions')

    def __str__(self):
        return self.name


@reversion.register()
class FlashActionsTaken(models.Model):
    """ All the actions taken by an organization in Flash Update """

    organization = models.CharField(
        choices=ActionOrg.choices,
        verbose_name=_('organization'), max_length=16,
    )
    actions = models.ManyToManyField(FlashAction, verbose_name=_('actions'), blank=True)
    summary = models.TextField(verbose_name=_('summary'), null=True, blank=True)
    flash_update = models.ForeignKey(
        FlashUpdate, verbose_name=_('flash update'), related_name='actions_taken_flash', on_delete=models.CASCADE
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('actions taken flash')
        verbose_name_plural = _('all actions taken flash')

    def __str__(self):
        return f'{self.organization} - {self.actions}'


@reversion.register()
class FlashEmailSubscriptions(models.Model):
    share_with = models.CharField(
        max_length=50, choices=FlashUpdate.FlashShareWith.choices,
        default=FlashUpdate.FlashShareWith.IFRC_SECRETARIAT,
        verbose_name=_('share with')
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='flash_email_subscription')

    class Meta:
        verbose_name = _('flash email subscription')

    def __str__(self):
        return self.share_with


@reversion.register()
class DonorGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('name'))

    def __str__(self):
        return self.name


@reversion.register()
class Donors(models.Model):
    organization_name = models.CharField(max_length=500, blank=True, null=True)
    first_name = models.CharField(max_length=300, blank=True, null=True)
    last_name = models.CharField(max_length=300, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    position = models.CharField(max_length=300, blank=True, null=True)
    groups = models.ManyToManyField(DonorGroup, verbose_name=_('donor group'), blank=True)

    class Meta:
        verbose_name = _('donor')

    def __str__(self):
        return self.organization_name


@reversion.register()
class FlashUpdateShare(models.Model):
    flash_update = models.ForeignKey(FlashUpdate, on_delete=models.CASCADE, related_name='flash_update_share')
    donors = models.ManyToManyField(Donors, blank=True)
    donor_groups = models.ManyToManyField(DonorGroup, blank=True)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)

    def __str__(self):
        return self.flash_update.title
