from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField

from enumfields import IntEnum, EnumIntegerField
from api.storage import get_storage


# Create your models here.
class ReferenceUrls(models.Model):
    url = models.URLField()


class InformalReferences(models.Model):
    date = models.DateTimeField(verbose_name=_('date'), blank=True)
    source_description = models.CharField(verbose_name=_('Name or Source Description'), max_length=225, blank=True)
    url = models.ManyToManyField(ReferenceUrls, verbose_name=_('Add url'), blank=True)


class InformalCountryDistrict(models.Model):
    from api.models import Country, District

    countries = models.ForeignKey(
        Country, verbose_name=_('countries'), on_delete=models.CASCADE,
        related_name='informal_country'
    )
    districts = models.ForeignKey(
        District, verbose_name=_('districts'), on_delete=models.CASCADE,
        related_name='informal_district'
    )


class ShareChoices(IntEnum):
    IFRC = 1
    RCRC = 2
    RCRC_DONOR = 3

    class Labels:
        IFRC = _('IFRC Secretariat')
        PUBLIC = _('RCRC Network')
        IFRC_NS = _('RCRC Network and Donors')


class InformalUpdate(models.Model):
    '''
    This is a base model for Informal Update

    '''
    from api.models import DisasterType

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

    # Focal Point
    originator_name = models.CharField(verbose_name=_('name'), max_length=100)
    originator_title = models.CharField(verbose_name=_('title'), max_length=300)
    originator_email = models.CharField(verbose_name=_('email'), max_length=300)
    originator_phone = models.CharField(verbose_name=_('phone'), max_length=50, blank=True)

    ifrc_name = models.CharField(verbose_name=_('name'), max_length=100)
    ifrc_title = models.CharField(verbose_name=_('title'), max_length=300)
    ifrc_email = models.CharField(verbose_name=_('email'), max_length=300)
    ifrc_phone = models.CharField(verbose_name=_('phone'), max_length=50, blank=True)

    # Share with
    visibility = EnumIntegerField(ShareChoices, verbose_name=_('share with'), default=1)

class GraphicMap(models.Model):
    class GraphicMapType(IntEnum):
        MAP = 0
        IMAGE = 1

        class Labels:
            MAP = _('Map')
            IMAGE = _('Image')

    informal_update = models.ForeignKey(
        InformalUpdate, verbose_name=_('Informal Update'), related_name='informal_graphic_map',
        on_delete=models.CASCADE)
    file = models.FileField(
        verbose_name=_('file'), null=True, blank=True, upload_to='graphic_map/%Y/%m/%d/', storage=get_storage()
    )
    caption = models.CharField(max_length=225, blank=True)
    file_type = EnumIntegerField(GraphicMapType, verbose_name=_('File type'))


class InformalAction(models.Model):
    """ Action taken for Informal Update """
    from api.models import ActionOrg, ActionType, ActionCategory

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

    class Meta:
        verbose_name = _('informal action')
        verbose_name_plural = _('informal actions')

    def __str__(self):
        return self.name


class InformalActionsTaken(models.Model):
    """ All the actions taken by an organization in Informal Update """
    from api.models import ActionOrg

    organization = models.CharField(
        choices=ActionOrg.CHOICES,
        verbose_name=_('organization'), max_length=16,
    )
    actions = models.ManyToManyField(InformalAction, verbose_name=_('actions'), blank=True)
    summary = models.TextField(verbose_name=_('summary'), blank=True)
    informal_update = models.ForeignKey(
        InformalUpdate, verbose_name=_('informal update'), related_name='actions_taken_informal', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('actions taken informal')
        verbose_name_plural = _('all actions taken informal')

    def __str__(self):
        return '%s: %s' % (self.get_organization_display(), self.summary)
