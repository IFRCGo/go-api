from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
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

from main.enums import TextChoices


class InformalGraphicMap(models.Model):
    file = models.FileField(
        verbose_name=_('file'),
        upload_to='informal_update/images/'
    )
    caption = models.CharField(max_length=225, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created_by'),
        on_delete=models.SET_NULL, null=True,
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('informal graphic map')
        verbose_name_plural = _('informal graphic maps')


class InformalReferences(models.Model):
    date = models.DateField(verbose_name=_('date'), blank=True)
    source_description = models.CharField(verbose_name=_('Name or Source Description'), max_length=225, blank=True)
    url = models.TextField(blank=True)
    document = models.ForeignKey(
        InformalGraphicMap, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('document'),
        related_name='informal_document'
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('informal reference')
        verbose_name_plural = _('informal references')

    def __str__(self):
        return f'{self.source_description} - {self.date}'


class InformalUpdate(models.Model):
    '''
    This is a base model for Informal Update
    '''

    class InformalShareWith(TextChoices):
        IFRC_SECRETARIAT = 'ifrc_secretariat', _('IFRC Secretariat')
        RCRC_NETWORK = 'rcrc_network', _('RCRC Network')
        RCRC_NETWORK_AND_DONOR = 'rcrc_network_and_donors', _('RCRC Network and Donors')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created by'), related_name='informal_update_created_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('modified by'), related_name='informal_update_modified_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('updated at'), auto_now=True)

    # context
    hazard_type = models.ForeignKey(
        DisasterType, verbose_name=_('hazard type'), related_name='informal_update_hazard_type',
        null=True, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=300)
    situational_overview = models.TextField(verbose_name=_('Situational Overview'))

    # map/graphics
    map = models.ManyToManyField(
        InformalGraphicMap, blank=True,
        verbose_name=_('map'),
        related_name='informal_map'
    )
    graphics = models.ManyToManyField(
        InformalGraphicMap, blank=True,
        verbose_name=_('graphics'),
        related_name='informal_graphics'
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
        max_length=50, choices=InformalShareWith.choices,
        null=True, blank=True, verbose_name=_('share with')
    )
    references = models.ManyToManyField(
        InformalReferences, blank=True,
        verbose_name=_('references')
    )

    class Meta:
        verbose_name = _('Informal update')
        verbose_name_plural = _('Informal updates')

    def __str__(self):
        return f'{self.title}'


class InformalCountryDistrict(models.Model):
    informal_update = models.ForeignKey(
        InformalUpdate, on_delete=models.CASCADE,
        verbose_name=_('informal update')
    )
    country = models.ForeignKey(
        Country, verbose_name=_('country'), on_delete=models.CASCADE,
        related_name='informal_country'
    )
    district = models.ForeignKey(
        District, verbose_name=_('district'), on_delete=models.CASCADE,
        related_name='informal_district'
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('informal_update', 'country')
        verbose_name = _('informal country district')
        verbose_name_plural = _('informal countries districts')

    def __str__(self):
        return f'{self.country} - {self.district}'


class InformalAction(models.Model):
    """ Action taken for Informal Update """

    name = models.CharField(verbose_name=_('name'), max_length=400)
    organizations = ArrayField(
        models.CharField(choices=ActionOrg.CHOICES, max_length=4),
        verbose_name=_('organizations'), default=list, blank=True
    )
    informal_update_types = ArrayField(
        models.CharField(choices=ActionType.CHOICES, max_length=16),
        verbose_name=_('informal update types'), default=list,
    )
    category = models.CharField(
        max_length=255, verbose_name=_('category'), choices=ActionCategory.CHOICES, default=ActionCategory.GENERAL
    )
    is_disabled = models.BooleanField(verbose_name=_('is disabled?'), default=False, help_text=_('Disable in form'))
    tooltip_text = models.TextField(verbose_name=_('tooltip text'), null=True, blank='true')
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('informal action')
        verbose_name_plural = _('informal actions')

    def __str__(self):
        return self.name


class InformalActionsTaken(models.Model):
    """ All the actions taken by an organization in Informal Update """

    organization = models.CharField(
        choices=ActionOrg.CHOICES,
        verbose_name=_('organization'), max_length=16,
    )
    actions = models.ManyToManyField(InformalAction, verbose_name=_('actions'), blank=True)
    summary = models.TextField(verbose_name=_('summary'), null=True, blank=True)
    informal_update = models.ForeignKey(
        InformalUpdate, verbose_name=_('informal update'), related_name='actions_taken_informal', on_delete=models.CASCADE
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('actions taken informal')
        verbose_name_plural = _('all actions taken informal')

    def __str__(self):
        return f'{self.organization} - {self.actions}'


class InformalEmailSubscriptions(models.Model):
    share_with = models.CharField(
        max_length=50, choices=InformalUpdate.InformalShareWith.choices,
        default=InformalUpdate.InformalShareWith.IFRC_SECRETARIAT,
        verbose_name=_('share with')
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='informal_email_subscription')

    def __str__(self):
        return self.share_with


class Donors(models.Model):
    organization_name = models.CharField(max_length=500, blank=True, null=True)
    first_name = models.CharField(max_length=300, blank=True, null=True)
    last_name = models.CharField(max_length=300, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    position = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.organization_name
