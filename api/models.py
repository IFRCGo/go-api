from django.utils.translation import ugettext_lazy as _
# from django.db import models
from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
# from django.db.models import Prefetch
from django.dispatch import receiver
from django.utils import timezone
from enumfields import IntEnum, EnumIntegerField
from .storage import get_storage
from tinymce import HTMLField
from django.core.validators import FileExtensionValidator, validate_slug
from django.contrib.postgres.fields import ArrayField
from datetime import datetime, timedelta
import pytz
from .utils import (
    validate_slug_number,
    # is_user_ifrc,
)


# Write model properties to dictionary
def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, models.ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values())
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class DisasterType(models.Model):
    """ summary of disaster """
    name = models.CharField(verbose_name=_('name'), max_length=100)
    summary = models.TextField(verbose_name=_('summary'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('disaster type')
        verbose_name_plural = _('disaster types')

    def __str__(self):
        return self.name


class RegionName(IntEnum):
    AFRICA = 0
    AMERICAS = 1
    ASIA_PACIFIC = 2
    EUROPE = 3
    MENA = 4

    # class Labels:
    #     AFRICA = _('Africa')
    #     AMERICAS = _('Americas')
    #     ASIA_PACIFIC = _('Asia Pacific')
    #     EUROPE = _('Europe')
    #     MENA = _('Middle East North Africa')


class Region(models.Model):
    """ A region """
    name = EnumIntegerField(RegionName, verbose_name=_('name'))
    bbox = models.PolygonField(srid=4326, blank=True, null=True)
    label = models.CharField(verbose_name=_('name of the region'), max_length=150, blank=True)

    def indexing(self):
        return {
            'id': self.id,
            'event_id': None,
            'type': 'region',
            'name': str(self.name.label),
            'keyword': None,
            'body': str(self.name.label),
            'date': None
        }

    def es_id(self):
        return 'region-%s' % self.id

    class Meta:
        ordering = ('name',)
        verbose_name = _('region')
        verbose_name_plural = _('regions')

    def __str__(self):
        return str(self.name.label)

    def region_name(self):
        return str(self.name)


def logo_document_path(instance, filename):
    return 'logos/%s/%s' % (instance.iso, filename)


class CountryType(IntEnum):
    '''
        We use the Country model for some things that are not "Countries". This helps classify the type.
    '''
    COUNTRY = 1
    CLUSTER = 2
    REGION = 3
    COUNTRY_OFFICE = 4
    REPRESENTATIVE_OFFICE = 5

    # class Labels:
    #     COUNTRY = _('Country')
    #     CLUSTER = _('Cluster')
    #     REGION = _('Region')
    #     COUNTRY_OFFICE = _('Country Office')
    #     REPRESENTATIVE_OFFICE = _('Representative Office')

    # select name, society_name, record_type from api_country where name like '%luster%';
    # select name, society_name, record_type from api_country where name like '%egion%';
    # select name, society_name, record_type from api_country where name like '%ffice%'; -- no result
    # update api_country set record_type=2 where name like '%luster%';
    # update api_country set record_type=3 where name like '%egion%';


class Country(models.Model):
    """ A country """

    name = models.CharField(verbose_name=_('name'), max_length=100)
    record_type = EnumIntegerField(CountryType, verbose_name=_('type'), default=1, help_text=_('Type of entity'))
    iso = models.CharField(verbose_name=_('ISO'), max_length=2, null=True)
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=3, null=True)
    society_name = models.TextField(verbose_name=_('society name'), blank=True)
    society_url = models.URLField(blank=True, verbose_name=_('URL - Society'))
    url_ifrc = models.URLField(blank=True, verbose_name=_('URL - IFRC'))
    region = models.ForeignKey(Region, verbose_name=_('region'), null=True, blank=True, on_delete=models.SET_NULL)
    overview = models.TextField(verbose_name=_('overview'), blank=True, null=True)
    key_priorities = models.TextField(verbose_name=_('key priorities'), blank=True, null=True)
    inform_score = models.DecimalField(verbose_name=_('inform score'), blank=True, null=True, decimal_places=2, max_digits=3)
    logo = models.FileField(
        blank=True, null=True, verbose_name=_('logo'), upload_to=logo_document_path,
        storage=get_storage(), validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'gif'])]
    )
    geom = models.MultiPolygonField(srid=4326, blank=True, null=True)
    centroid = models.PointField(srid=4326, blank=True, null=True)
    bbox = models.PolygonField(srid=4326, blank=True, null=True)
    independent = models.NullBooleanField(
        default=None, null=True, help_text=_('Is this an independent country?')
    )
    is_deprecated = models.BooleanField(
        default=False, help_text=_('Is this an active, valid country?')
    )

    # Population Data From WB API
    wb_population = models.PositiveIntegerField(
        verbose_name=_('WB population'), null=True, blank=True, help_text=_('population data from WB API')
    )
    wb_year = models.CharField(
        verbose_name=_('WB Year'), max_length=4, null=True, blank=True, help_text=_('population data year from WB API')
    )

    def indexing(self):
        return {
            'id': self.id,
            'event_id': None,
            'type': 'country',
            'name': self.name,
            'keyword': None,
            'body': '%s %s' % (
                self.name,
                self.society_name,
            ),
            'date': None
        }

    def es_id(self):
        return 'country-%s' % self.id

    class Meta:
        ordering = ('name',)
        verbose_name = _('country')
        verbose_name_plural = _('countries')

    def __str__(self):
        return self.name


class District(models.Model):
    """ Admin level 1 field """

    name = models.CharField(verbose_name=_('name'), max_length=100)
    code = models.CharField(verbose_name=_('code'), max_length=10)
    country = models.ForeignKey(Country, verbose_name=_('country'), null=True, on_delete=models.SET_NULL)
    country_iso = models.CharField(verbose_name=_('country ISO2'), max_length=2, null=True)
    country_name = models.CharField(verbose_name=_('country name'), max_length=100)
    is_enclave = models.BooleanField(
        verbose_name=_('is enclave?'), default=False, help_text=_('Is it an enclave away from parent country?')
    )  # used to mark if the district is far away from the country
    geom = models.MultiPolygonField(srid=4326, blank=True, null=True)
    centroid = models.PointField(srid=4326, blank=True, null=True)
    bbox = models.PolygonField(srid=4326, blank=True, null=True)
    is_deprecated = models.BooleanField(
        default=False, help_text=_('Is this an active, valid district?')
    )
    # Population Data From WB API
    wb_population = models.PositiveIntegerField(
        verbose_name=_('WB population'), null=True, blank=True, help_text=_('population data from WB API')
    )
    wb_year = models.CharField(
        verbose_name=_('WB year'), max_length=4, null=True, blank=True, help_text=_('population data year from WB API')
    )

    class Meta:
        ordering = ('code',)
        verbose_name = _('district')
        verbose_name_plural = _('districts')

    def __str__(self):
        return '%s - %s' % (self.country_name, self.name)


class VisibilityChoices(IntEnum):
    MEMBERSHIP = 1
    IFRC = 2
    PUBLIC = 3

    # class Labels:
    #     MEMBERSHIP = _('Membership')
    #     IFRC = _('IFRC Only')
    #     PUBLIC = _('Public')


class VisibilityCharChoices():
    """Same as VisibilityChoices but using char instead of Enum"""
    MEMBERSHIP = 'logged_in_user'
    IFRC = 'ifrc_only'
    PUBLIC = 'public'

    CHOICES = (
        (MEMBERSHIP, _('Membership')),
        (IFRC, _('IFRC Only')),
        (PUBLIC, _('Public')),
    )


# Common parent class for key figures.
# Country/region variants inherit from this.
class AdminKeyFigure(models.Model):
    figure = models.CharField(verbose_name=_('figure'), max_length=100)
    deck = models.CharField(verbose_name=_('deck'), max_length=50)
    source = models.CharField(verbose_name=_('source'), max_length=256)
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=3)

    class Meta:
        ordering = ('source',)
        verbose_name = _('admin key figure')
        verbose_name_plural = _('admin key figures')

    def __str__(self):
        return self.source


class RegionKeyFigure(AdminKeyFigure):
    region = models.ForeignKey(Region, verbose_name=_('region'), related_name='key_figures', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('region key figure')
        verbose_name_plural = _('region key figures')


class CountryKeyFigure(AdminKeyFigure):
    country = models.ForeignKey(Country, verbose_name=_('country'), related_name='key_figures', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('country key figure')
        verbose_name_plural = _('country key figures')


class PositionType(IntEnum):
    TOP = 1
    HIGH = 2
    MIDDLE = 3
    LOW = 4
    BOTTOM = 5

    # class Labels:
    #     TOP = _('Top')
    #     HIGH = _('High')
    #     MIDDLE = _('Middle')
    #     LOW = _('Low')
    #     BOTTOM = _('Bottom')


class TabNumber(IntEnum):
    TAB_1 = 1
    TAB_2 = 2
    TAB_3 = 3

    # class Labels:
    #     TAB_1 = _('Tab 1')
    #     TAB_2 = _('Tab 2')
    #     TAB_3 = _('Tab 3')


class RegionSnippet(models.Model):
    region = models.ForeignKey(Region, verbose_name=_('region'), related_name='snippets', on_delete=models.CASCADE)
    snippet = HTMLField(verbose_name=_('snippet'), null=True, blank=True)
    image = models.ImageField(
        verbose_name=_('image'), null=True, blank=True, upload_to='regions/%Y/%m/%d/', storage=get_storage()
    )
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=3)
    position = EnumIntegerField(PositionType, verbose_name=_('position'), default=3)

    class Meta:
        ordering = ('position', 'id',)
        verbose_name = _('region snippet')
        verbose_name_plural = _('region snippets')

    def __str__(self):
        return self.snippet


class CountrySnippet(models.Model):
    country = models.ForeignKey(Country, verbose_name=_('country'), related_name='snippets', on_delete=models.CASCADE)
    snippet = HTMLField(verbose_name=_('snippet'), null=True, blank=True)
    image = models.ImageField(
        verbose_name=_('image'), null=True, blank=True, upload_to='countries/%Y/%m/%d/', storage=get_storage()
    )
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=3)
    position = EnumIntegerField(PositionType, verbose_name=_('position'), default=3)

    class Meta:
        ordering = ('position', 'id',)
        verbose_name = _('country snippet')
        verbose_name_plural = _('country snippets')

    def __str__(self):
        return self.snippet


class AdminLink(models.Model):
    title = models.CharField(verbose_name=_('title'), max_length=100)
    url = models.URLField(verbose_name=_('url'), max_length=300)

    class Meta:
        verbose_name = _('admin link')
        verbose_name_plural = _('admin links')


class RegionLink(AdminLink):
    region = models.ForeignKey(Region, verbose_name=_('region'), related_name='links', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('region link')
        verbose_name_plural = _('region links')


class CountryLink(AdminLink):
    country = models.ForeignKey(Country, verbose_name=_('country'), related_name='links', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('country link')
        verbose_name_plural = _('country links')


class AdminContact(models.Model):
    ctype = models.CharField(verbose_name=_('type'), max_length=100, blank=True)
    name = models.CharField(verbose_name=_('name'), max_length=100)
    title = models.CharField(verbose_name=_('title'), max_length=300)
    email = models.CharField(verbose_name=_('email'), max_length=300)

    class Meta:
        verbose_name = _('admin contact')
        verbose_name_plural = _('admin contacts')

    def __str__(self):
        return self.name


class RegionContact(AdminContact):
    region = models.ForeignKey(Region, verbose_name=_('region'), related_name='contacts', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('region contact')
        verbose_name_plural = _('region contacts')


class CountryContact(AdminContact):
    country = models.ForeignKey(Country, verbose_name=_('country'), related_name='contacts', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('country contact')
        verbose_name_plural = _('country contacts')


class AlertLevel(IntEnum):
    GREEN = 0
    ORANGE = 1
    RED = 2

    # class Labels:
    #     GREEN = _('Green')
    #     ORANGE = _('Orange')
    #     RED = _('Red')


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    name = models.CharField(verbose_name=_('name'), max_length=100)
    # FIXME slug is not editable until we resolve https://github.com/IFRCGo/go-frontend/issues/1013
    slug = models.CharField(
        verbose_name=_('slug'), max_length=50, editable=False, default=None, unique=True, null=True, blank=True,
        validators=[validate_slug, validate_slug_number],
        help_text=_(
            'Optional string for a clean URL. For example, go.ifrc.org/emergencies/hurricane-katrina-2019.'
            ' The string cannot start with a number and is forced to be lowercase.'
            ' Recommend using hyphens over underscores. Special characters like # is not allowed.'
        )
    )
    dtype = models.ForeignKey(DisasterType, verbose_name=_('disaster type'), null=True, on_delete=models.SET_NULL)
    districts = models.ManyToManyField(District, verbose_name=_('districts'), blank=True)
    countries = models.ManyToManyField(Country, verbose_name=_('countries'))
    regions = models.ManyToManyField(Region, verbose_name=_('regions'))
    parent_event = models.ForeignKey(
        'self', null=True, blank=True, verbose_name=_('Parent Emergency'), on_delete=models.SET_NULL,
        help_text=_(
            'If needed, you have to change the connected Appeals\', Field Reports\','
            ' etc to point to the parent Emergency manually.'
        )
    )
    summary = HTMLField(verbose_name=_('summary'), blank=True, default='')

    num_injured = models.IntegerField(verbose_name=_('number of injured'), null=True, blank=True)
    num_dead = models.IntegerField(verbose_name=_('number of dead'), null=True, blank=True)
    num_missing = models.IntegerField(verbose_name=_('number of missing'), null=True, blank=True)
    num_affected = models.IntegerField(verbose_name=_('number of affected'), null=True, blank=True)
    num_displaced = models.IntegerField(verbose_name=_('name'), null=True, blank=True)

    ifrc_severity_level = EnumIntegerField(AlertLevel, default=0, verbose_name=_('IFRC Severity level'))
    glide = models.CharField(verbose_name=_('glide'), max_length=18, blank=True)

    disaster_start_date = models.DateTimeField(verbose_name=_('disaster start date'))
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('updated at'), auto_now=True)
    previous_update = models.DateTimeField(verbose_name=_('previous update'), null=True, blank=True)

    auto_generated = models.BooleanField(verbose_name=_('auto generated'), default=False, editable=False)
    auto_generated_source = models.CharField(
        verbose_name=_('auto generated source'), max_length=50, null=True, blank=True, editable=False
    )

    # Meant to give the organization a way of highlighting certain, important events.
    is_featured = models.BooleanField(default=False, verbose_name=_('is featured on home page'))

    # Allows admins to feature the Event on the region page.
    is_featured_region = models.BooleanField(default=False, verbose_name=_('is featured on region page'))

    hide_attached_field_reports = models.BooleanField(verbose_name=_('hide attached field reports?'), default=False)

    # Tabs. Events can have upto 3 tabs to organize snippets.
    tab_one_title = models.CharField(
        verbose_name=_('tab one title'), max_length=50, null=False, blank=True, default='Additional Information'
    )
    tab_two_title = models.CharField(verbose_name=_('tab two title'), max_length=50, null=True, blank=True)
    tab_three_title = models.CharField(verbose_name=_('tab three title'), max_length=50, null=True, blank=True)

    class Meta:
        ordering = ('-disaster_start_date',)
        verbose_name = _('emergency')
        verbose_name_plural = _('emergencies')

    # @staticmethod
    # def get_for(user):
    #     field_report_pretech = Prefetch('field_reports', queryset=FieldReport.get_for(user))
    #     return Event.objects.prefetch_related(field_report_pretech)

    def start_date(self):
        """ Get start date of first appeal """
        start_dates = [getattr(a, 'start_date') for a in self.appeals.all()]
        return min(start_dates) if len(start_dates) else None

    def end_date(self):
        """ Get latest end date of all appeals """
        end_dates = [getattr(a, 'end_date') for a in self.appeals.all()]
        return max(end_dates) if len(end_dates) else None

    def indexing(self):
        countries = [getattr(c, 'name') for c in self.countries.all()]
        return {
            'id': self.id,
            'event_id': self.id,
            'type': 'event',
            'name': self.name,
            'keyword': None,
            'body': '%s %s' % (
                self.name,
                ' '.join(map(str, countries)) if len(countries) else None,
            ),
            'date': self.disaster_start_date,
        }

    def es_id(self):
        return 'event-%s' % self.id

    def record_type(self):
        return 'EVENT'

    def to_dict(self):
        return to_dict(self)

    def save(self, *args, **kwargs):

        # Make the slug lowercase
        if self.slug:
            self.slug = self.slug.lower()

        # On save, if `disaster_start_date` is not set, make it the current time
        if not self.id and not self.disaster_start_date:
            self.disaster_start_date = timezone.now()

        return super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class EventContact(models.Model):
    """ Contact for event """

    ctype = models.CharField(verbose_name=_('type'), max_length=100, blank=True)
    name = models.CharField(verbose_name=_('name'), max_length=100)
    title = models.CharField(verbose_name=_('title'), max_length=300)
    email = models.CharField(verbose_name=_('email'), max_length=300)
    phone = models.CharField(verbose_name=_('phone'), max_length=100, blank=True, null=True)
    event = models.ForeignKey(Event, verbose_name=_('event'), related_name='contacts', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('event contact')
        verbose_name_plural = _('event contacts')

    def __str__(self):
        return '%s: %s' % (self.name, self.title)


class KeyFigure(models.Model):
    event = models.ForeignKey(Event, verbose_name=_('event'), related_name='key_figures', on_delete=models.CASCADE)
    number = models.CharField(verbose_name=_('number'), max_length=100, help_text=_('key figure metric'))
    deck = models.CharField(verbose_name=_('deck'), max_length=50, help_text=_('key figure units'))
    source = models.CharField(verbose_name=_('source'), max_length=256, help_text=_('key figure website link, publication'))

    class Meta:
        verbose_name = _('key figure')
        verbose_name_plural = _('key figures')


def snippet_image_path(instance, filename):
    return 'emergencies/%s/%s' % (instance.event.id, filename)


class Snippet(models.Model):
    """ Snippet of text """
    snippet = HTMLField(verbose_name=_('snippet'), null=True, blank=True)
    image = models.ImageField(
        verbose_name=_('image'), null=True, blank=True, upload_to=snippet_image_path, storage=get_storage()
    )
    event = models.ForeignKey(Event, verbose_name=_('event'), related_name='snippets', on_delete=models.CASCADE)
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=3)
    position = EnumIntegerField(PositionType, verbose_name=_('position'), default=3)
    tab = EnumIntegerField(TabNumber, verbose_name=_('tab'), default=1)

    class Meta:
        ordering = ('position', 'id',)
        verbose_name = _('snippet')
        verbose_name_plural = _('snippets')

    def __str__(self):
        return self.snippet


class SituationReportType(models.Model):
    """ Document type, to be able to filter Situation Reports """
    type = models.CharField(verbose_name=_('type'), max_length=50)
    is_primary = models.BooleanField(
        verbose_name=_('is primary?'), default=False, editable=False,
        help_text=_('Ensure this type gets precedence over others that are empty')
    )

    class Meta:
        verbose_name = _('situation report type')
        verbose_name_plural = _('situation report types')

    def __str__(self):
        return self.type


def sitrep_document_path(instance, filename):
    return 'sitreps/%s/%s' % (instance.event.id, filename)


class SituationReport(models.Model):
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    name = models.CharField(verbose_name=_('name'), max_length=100)
    document = models.FileField(
        verbose_name=_('document'), null=True, blank=True, upload_to=sitrep_document_path, storage=get_storage()
    )
    document_url = models.URLField(verbose_name=_('document url'), blank=True)

    event = models.ForeignKey(Event, verbose_name=_('event'), on_delete=models.CASCADE)
    type = models.ForeignKey(
        SituationReportType, verbose_name=_('type'), related_name='situation_reports', null=True, on_delete=models.SET_NULL
    )
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=VisibilityChoices.MEMBERSHIP)
    is_pinned = models.BooleanField(verbose_name=_('is pinned?'), default=False, help_text=_('pin this report at the top'))

    class Meta:
        verbose_name = _('situation report')
        verbose_name_plural = _('situation reports')

    def __str__(self):
        return '%s - %s' % (self.event, self.name)


class GDACSEvent(models.Model):
    """ A GDACS type event, from alerts """

    eventid = models.CharField(verbose_name=_('event id'), max_length=12)
    title = models.TextField(verbose_name=_('title'))
    description = models.TextField(verbose_name=_('description'))
    image = models.URLField(verbose_name=_('image'), null=True)
    report = models.URLField(verbose_name=_('report'), null=True)
    publication_date = models.DateTimeField(verbose_name=_('publication date'))
    year = models.IntegerField(verbose_name=_('year'))
    lat = models.FloatField(verbose_name=_('latitude'))
    lon = models.FloatField(verbose_name=_('longitude'))
    event_type = models.CharField(verbose_name=_('event type'), max_length=16)
    alert_level = EnumIntegerField(AlertLevel, verbose_name=_('alert level'), default=0)
    alert_score = models.CharField(verbose_name=_('alert score'), max_length=16, null=True)
    severity = models.TextField(verbose_name=_('severity'))
    severity_unit = models.CharField(verbose_name=_('severity unit'), max_length=16)
    severity_value = models.CharField(verbose_name=_('severity value'), max_length=16)
    population_unit = models.CharField(verbose_name=_('population unit'), max_length=16)
    population_value = models.CharField(verbose_name=_('population value'), max_length=16)
    vulnerability = models.FloatField(verbose_name=_('vulnerability'))
    countries = models.ManyToManyField(Country, verbose_name=_('countries'))
    country_text = models.TextField(verbose_name=_('country text'))

    class Meta:
        verbose_name = _('gdacs event')
        verbose_name_plural = _('gdacs events')

    def __str__(self):
        return self.title


class AppealType(IntEnum):
    """ summarys of appeals """
    DREF = 0
    APPEAL = 1
    INTL = 2

    # class Labels:
    #     DREF = _('DREF')
    #     APPEAL = _('Emergency Appeal')
    #     INTL = _('International Appeal')


class AppealStatus(IntEnum):
    ACTIVE = 0
    CLOSED = 1
    FROZEN = 2
    ARCHIVED = 3

    # class Labels:
    #     ACTIVE = _('Active')
    #     CLOSED = _('Closed')
    #     FROZEN = _('Frozen')
    #     ARCHIVED = _('Archived')


class Appeal(models.Model):
    """ An appeal for a disaster and country, containing documents """

    # appeal ID, assinged by creator
    aid = models.CharField(verbose_name=_('appeal ID'), max_length=20)
    name = models.CharField(verbose_name=_('name'), max_length=100)
    dtype = models.ForeignKey(DisasterType, verbose_name=_('disaster type'), null=True, on_delete=models.SET_NULL)
    atype = EnumIntegerField(AppealType, verbose_name=_('appeal type'), default=0)

    status = EnumIntegerField(AppealStatus, verbose_name=_('status'), default=0)
    code = models.CharField(verbose_name=_('code'), max_length=20, null=True, unique=True)
    sector = models.CharField(verbose_name=_('sector'), max_length=100, blank=True)

    num_beneficiaries = models.IntegerField(verbose_name=_('number of beneficiaries'), default=0)
    amount_requested = models.DecimalField(verbose_name=_('amount requested'), max_digits=12, decimal_places=2, default=0.00)
    amount_funded = models.DecimalField(verbose_name=_('amount funded'), max_digits=12, decimal_places=2, default=0.00)

    start_date = models.DateTimeField(verbose_name=_('start date'), null=True)
    end_date = models.DateTimeField(verbose_name=_('end date'), null=True)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('modified at'), auto_now=True)
    previous_update = models.DateTimeField(verbose_name=_('previous update'), null=True, blank=True)
    real_data_update = models.DateTimeField(verbose_name=_('real data update'), null=True, blank=True)

    event = models.ForeignKey(
        Event, verbose_name=_('event'), related_name='appeals', null=True, blank=True, on_delete=models.SET_NULL
    )
    needs_confirmation = models.BooleanField(verbose_name=_('needs confirmation?'), default=False)
    country = models.ForeignKey(Country, verbose_name=_('country'), null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, verbose_name=_('region'), null=True, on_delete=models.SET_NULL)

    # NOTE: This field doesn't exists (No translation added)
    # Supplementary fields
    # These aren't included in the ingest, and are
    # entered manually by IFRC staff
    shelter_num_people_targeted: models.IntegerField(null=True, blank=True)
    shelter_num_people_reached: models.IntegerField(null=True, blank=True)
    shelter_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    basic_needs_num_people_targeted: models.IntegerField(null=True, blank=True)
    basic_needs_num_people_reached: models.IntegerField(null=True, blank=True)
    basic_needs_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    health_num_people_targeted: models.IntegerField(null=True, blank=True)
    health_num_people_reached: models.IntegerField(null=True, blank=True)
    health_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    water_sanitation_num_people_targeted: models.IntegerField(null=True, blank=True)
    water_sanitation_num_people_reached: models.IntegerField(null=True, blank=True)
    water_sanitation_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    gender_inclusion_num_people_targeted: models.IntegerField(null=True, blank=True)
    gender_inclusion_num_people_reached: models.IntegerField(null=True, blank=True)
    gender_inclusion_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    migration_num_people_targeted: models.IntegerField(null=True, blank=True)
    migration_num_people_reached: models.IntegerField(null=True, blank=True)
    migration_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    risk_reduction_num_people_targeted: models.IntegerField(null=True, blank=True)
    risk_reduction_num_people_reached: models.IntegerField(null=True, blank=True)
    risk_reduction_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    strenghtening_national_society_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    international_disaster_response_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    influence_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    accountable_ifrc_budget: models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        ordering = ('-start_date', '-end_date',)
        verbose_name = _('appeal')
        verbose_name_plural = _('appeals')

    def indexing(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'type': 'appeal',
            'name': self.name,
            'keyword': self.code,
            'body': '%s %s' % (
                self.name,
                getattr(self.country, 'name', None)
            ),
            'date': self.start_date,
        }

    def es_id(self):
        return 'appeal-%s' % self.id

    def record_type(self):
        return 'APPEAL'

    def to_dict(self):
        data = to_dict(self)
        data['atype'] = str(self.atype.label)
        data['country'] = self.country.name
        return data

    def __str__(self):
        return self.code


def appeal_document_path(instance, filename):
    return 'appeals/%s/%s' % (instance.appeal, filename)


class AppealDocument(models.Model):
    # Don't set `auto_now_add` so we can modify it on save
    created_at = models.DateTimeField(verbose_name=_('created at'))
    name = models.CharField(verbose_name=_('name'), max_length=100)
    document = models.FileField(
        verbose_name=_('document'), null=True, blank=True, upload_to=appeal_document_path, storage=get_storage()
    )
    document_url = models.URLField(verbose_name=_('document url'), blank=True)

    appeal = models.ForeignKey(Appeal, verbose_name=_('appeal'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('appeal document')
        verbose_name_plural = _('appeal documents')

    def save(self, *args, **kwargs):
        # On save, if `created` is not set, make it the current time
        if not self.id and not self.created_at:
            self.created_at = timezone.now()
        return super(AppealDocument, self).save(*args, **kwargs)

    def __str__(self):
        return '%s - %s' % (self.appeal, self.name)


class RequestChoices(IntEnum):
    NO = 0
    REQUESTED = 1
    PLANNED = 2
    COMPLETE = 3

    # class Labels:
    #     NO = _('No')
    #     REQUESTED = _('Requested')
    #     PLANNED = _('Planned')
    #     COMPLETE = _('Complete')


class EPISourceChoices(IntEnum):
    MINISTRY_OF_HEALTH = 0
    WHO = 1
    OTHER = 2

    # class Labels:
    #     MINISTRY_OF_HEALTH = _('Ministry of health')
    #     WHO = _('WHO')
    #     OTHER = _('OTHER')


class FieldReport(models.Model):
    """ A field report for a disaster and country, containing documents """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('user'), related_name='user',
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    is_covid_report = models.BooleanField(
        verbose_name=_('is covid report?'),
        default=False,
        help_text=_('Is this a Field Report specific to the COVID-19 emergency?')
    )

    # Used to differentiate reports that have and have not been synced from DMIS
    rid = models.CharField(verbose_name=_('r id'), max_length=100, null=True, blank=True, editable=False)
    summary = models.TextField(verbose_name=_('summary'), blank=True)
    description = HTMLField(verbose_name=_('description'), blank=True, default='')
    dtype = models.ForeignKey(DisasterType, verbose_name=_('disaster type'), on_delete=models.PROTECT)
    event = models.ForeignKey(
        Event, verbose_name=_('event'), related_name='field_reports', null=True, blank=True, on_delete=models.SET_NULL
    )
    districts = models.ManyToManyField(District, verbose_name=_('districts'), blank=True)
    countries = models.ManyToManyField(Country, verbose_name=_('countries'))
    regions = models.ManyToManyField(Region, verbose_name=_('regions'), blank=True)
    status = models.IntegerField(verbose_name=_('status'), default=0)
    request_assistance = models.BooleanField(verbose_name=_('request assistance'), default=False)
    ns_request_assistance = models.BooleanField(verbose_name=_('NS request assistance'), default=False)

    num_injured = models.IntegerField(verbose_name=_('number of injured'), null=True, blank=True)
    num_dead = models.IntegerField(verbose_name=_('number of dead'), null=True, blank=True)
    num_missing = models.IntegerField(verbose_name=_('number of missing'), null=True, blank=True)
    num_affected = models.IntegerField(verbose_name=_('number of affected'), null=True, blank=True)
    num_displaced = models.IntegerField(verbose_name=_('number of displaced'), null=True, blank=True)
    num_assisted = models.IntegerField(verbose_name=_('number of assisted'), null=True, blank=True)
    num_localstaff = models.IntegerField(verbose_name=_('number of localstaff'), null=True, blank=True)
    num_volunteers = models.IntegerField(verbose_name=_('number of volunteers'), null=True, blank=True)
    num_expats_delegates = models.IntegerField(verbose_name=_('number of expatriate delegates'), null=True, blank=True)

    # Early Warning fields
    num_potentially_affected = models.IntegerField(verbose_name=_('number of potentially affected'), null=True, blank=True)
    num_highest_risk = models.IntegerField(verbose_name=_('number of highest risk'), null=True, blank=True)
    affected_pop_centres = models.CharField(verbose_name=_('affected population centres'), max_length=512, blank=True, null=True)

    gov_num_injured = models.IntegerField(verbose_name=_('number of injured (goverment)'), null=True, blank=True)
    gov_num_dead = models.IntegerField(verbose_name=_('number of dead (goverment)'), null=True, blank=True)
    gov_num_missing = models.IntegerField(verbose_name=_('number of missing (goverment)'), null=True, blank=True)
    gov_num_affected = models.IntegerField(verbose_name=_('number of affected (goverment)'), null=True, blank=True)
    gov_num_displaced = models.IntegerField(verbose_name=_('number of displaced (goverment)'), null=True, blank=True)
    gov_num_assisted = models.IntegerField(verbose_name=_('number of assisted (goverment)'), null=True, blank=True)

    # Epidemic fields
    epi_cases = models.IntegerField(verbose_name=_('number of cases (epidemic)'), null=True, blank=True)
    epi_suspected_cases = models.IntegerField(verbose_name=_('number of suspected cases (epidemic)'), null=True, blank=True)
    epi_probable_cases = models.IntegerField(verbose_name=_('number of probable cases (epidemic)'), null=True, blank=True)
    epi_confirmed_cases = models.IntegerField(verbose_name=_('number of confirmed cases (epidemic)'), null=True, blank=True)
    epi_num_dead = models.IntegerField(verbose_name=_('number of dead (epidemic)'), null=True, blank=True)
    epi_figures_source = EnumIntegerField(EPISourceChoices, verbose_name=_('figures source (epidemic)'), null=True, blank=True)

    who_num_assisted = models.IntegerField(verbose_name=_('number of assisted (who)'), null=True, blank=True)
    health_min_num_assisted = models.IntegerField(verbose_name=_('number of assisted (who)'), null=True, blank=True)

    # Early Warning fields
    gov_num_potentially_affected = models.IntegerField(verbose_name=_('potentially affected (goverment)'), null=True, blank=True)
    gov_num_highest_risk = models.IntegerField(verbose_name=_('people at highest risk (goverment)'), null=True, blank=True)
    gov_affected_pop_centres = models.CharField(
        verbose_name=_('affected population centres (goverment)'), max_length=512, blank=True, null=True)

    other_num_injured = models.IntegerField(verbose_name=_('number of injured (other)'), null=True, blank=True)
    other_num_dead = models.IntegerField(verbose_name=_('number of dead (other)'), null=True, blank=True)
    other_num_missing = models.IntegerField(verbose_name=_('number of missing (other)'), null=True, blank=True)
    other_num_affected = models.IntegerField(verbose_name=_('number of affected (other)'), null=True, blank=True)
    other_num_displaced = models.IntegerField(verbose_name=_('number of displace (other)'), null=True, blank=True)
    other_num_assisted = models.IntegerField(verbose_name=_('number of assisted (other)'), null=True, blank=True)

    # Early Warning fields
    other_num_potentially_affected = models.IntegerField(
        verbose_name=_('number of potentially affected (other)'), null=True, blank=True)
    other_num_highest_risk = models.IntegerField(verbose_name=_('number of highest risk (other)'), null=True, blank=True)
    other_affected_pop_centres = models.CharField(
        verbose_name=_('number of affected population centres (other)'), max_length=512, blank=True, null=True)

    # Date of data for situation fields
    sit_fields_date = models.DateTimeField(verbose_name=_('situation fields date'), blank=True, null=True)

    # Text field for users to specify sources for where they have marked 'Other' as source.
    other_sources = models.TextField(verbose_name=_('sources (other)'), blank=True, default='')

    # actions taken
    actions_others = models.TextField(verbose_name=_('actions taken (others)'), null=True, blank=True)

    # visibility
    visibility = EnumIntegerField(VisibilityChoices, verbose_name=_('visibility'), default=1)

    # information
    bulletin = EnumIntegerField(RequestChoices, verbose_name=_('bullentin'), default=0)
    dref = EnumIntegerField(RequestChoices, verbose_name=_('DREF'), default=0)
    dref_amount = models.IntegerField(verbose_name=_('DREF amount'), null=True, blank=True)
    appeal = EnumIntegerField(RequestChoices, verbose_name=_('appeal'), default=0)
    appeal_amount = models.IntegerField(verbose_name=_('appeal amount'), null=True, blank=True)
    imminent_dref = EnumIntegerField(RequestChoices, verbose_name=_('imminent dref'), default=0)  # only EW
    imminent_dref_amount = models.IntegerField(null=True, verbose_name=_('imminent dref amount'), blank=True)  # only EW
    forecast_based_action = EnumIntegerField(RequestChoices, verbose_name=_('forecast based action'), default=0)  # only EW
    forecast_based_action_amount = models.IntegerField(
        verbose_name=_('forecast based action amount'), null=True, blank=True)  # only EW

    # disaster response
    rdrt = EnumIntegerField(RequestChoices, verbose_name=_('RDRT'), default=0)
    num_rdrt = models.IntegerField(verbose_name=_('number of RDRT'), null=True, blank=True)
    fact = EnumIntegerField(RequestChoices, verbose_name=_('fact'), default=0)
    num_fact = models.IntegerField(verbose_name=_('number of fact'), null=True, blank=True)
    ifrc_staff = EnumIntegerField(RequestChoices, verbose_name=_('IFRC staff'), default=0)
    num_ifrc_staff = models.IntegerField(verbose_name=_('number of IFRC staff'), null=True, blank=True)

    # ERU units
    eru_base_camp = EnumIntegerField(RequestChoices, verbose_name=_('ERU base camp'), default=0)
    eru_base_camp_units = models.IntegerField(verbose_name=_('ERU base camp units'), null=True, blank=True)

    eru_basic_health_care = EnumIntegerField(RequestChoices, verbose_name=_('ERU basic health care'), default=0)
    eru_basic_health_care_units = models.IntegerField(null=True, verbose_name=_('ERU basic health units'), blank=True)

    eru_it_telecom = EnumIntegerField(RequestChoices, verbose_name=_('ERU IT telecom'), default=0)
    eru_it_telecom_units = models.IntegerField(verbose_name=_('ERU IT telecom units'), null=True, blank=True)

    eru_logistics = EnumIntegerField(RequestChoices, verbose_name=_('ERU logistics'), default=0)
    eru_logistics_units = models.IntegerField(verbose_name=_('ERU logistics units'), null=True, blank=True)

    eru_deployment_hospital = EnumIntegerField(RequestChoices, verbose_name=_('ERU deployment hospital'), default=0)
    eru_deployment_hospital_units = models.IntegerField(verbose_name=_('ERU deployment hospital units'), null=True, blank=True)

    eru_referral_hospital = EnumIntegerField(RequestChoices, verbose_name=_('ERU referral hospital'), default=0)
    eru_referral_hospital_units = models.IntegerField(verbose_name=_('ERU referral hospital units'), null=True, blank=True)

    eru_relief = EnumIntegerField(RequestChoices, verbose_name=_('ERU relief'), default=0)
    eru_relief_units = models.IntegerField(null=True, verbose_name=_('ERU relief units'), blank=True)

    eru_water_sanitation_15 = EnumIntegerField(RequestChoices, verbose_name=_('ERU water sanitaion M15'), default=0)
    eru_water_sanitation_15_units = models.IntegerField(verbose_name=_('ERU water sanitaion M15 units'), null=True, blank=True)

    eru_water_sanitation_40 = EnumIntegerField(RequestChoices, verbose_name=_('ERU water sanitaion M40'), default=0)
    eru_water_sanitation_40_units = models.IntegerField(verbose_name=_('ERU water sanitaion M40 units'), null=True, blank=True)

    eru_water_sanitation_20 = EnumIntegerField(RequestChoices, verbose_name=_('ERU water sanitaion MSM20'), default=0)
    eru_water_sanitation_20_units = models.IntegerField(verbose_name=_('ERU water sanitaion MSM20 units'), null=True, blank=True)

    # start_date is now what the user explicitly sets while filling the Field Report form.
    start_date = models.DateTimeField(verbose_name=_('start date'), blank=True, null=True)

    # Created, updated at correspond to when the report entered this system.
    # Report date is when historical reports were created.
    # For reports that are not historical, it will be equal to created_at.
    report_date = models.DateTimeField(verbose_name=_('report date'), null=True, editable=False)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('updated at'), auto_now=True)
    previous_update = models.DateTimeField(verbose_name=_('previous updated at'), null=True, blank=True)

    class Meta:
        ordering = ('-created_at', '-updated_at',)
        verbose_name = _('field report')
        verbose_name_plural = _('field reports')

    # @staticmethod
    # def get_for(user):
    #     filters = models.Q(visibility=VisibilityChoices.PUBLIC)
    #     if user.is_authenticated:
    #         filters = models.Q(visibility__in=[VisibilityChoices.MEMBERSHIP, VisibilityChoices.PUBLIC])
    #         if is_user_ifrc(user):
    #             filters = models.Q()
    #     return FieldReport.objects.filter(filters)

    def save(self, *args, **kwargs):
        # On save, is report_date or start_date is not set, set it to now.
        if not self.id and not self.report_date:
            self.report_date = timezone.now()
        if not self.id and not self.start_date:
            self.start_date = timezone.now()
        return super(FieldReport, self).save(*args, **kwargs)

    def indexing(self):
        countries = [c.name for c in self.countries.all()]
        return {
            'id': self.id,
            'event_id': self.event_id,
            'type': 'report',
            'name': self.summary,
            'keyword': None,
            'body': '%s %s' % (
                self.summary,
                ' '.join(map(str, countries)) if len(countries) else None
            ),
            'date': self.created_at,
        }

    def es_id(self):
        return 'fieldreport-%s' % self.id

    def record_type(self):
        return 'FIELD_REPORT'

    def to_dict(self):
        return to_dict(self)

    def __str__(self):
        summary = self.summary if self.summary is not None else 'Summary not available'
        return '%s - %s' % (self.id, summary)


class FieldReportContact(models.Model):
    """ Contact for field report """

    ctype = models.CharField(verbose_name=_('type'), max_length=100, blank=True)
    name = models.CharField(verbose_name=_('name'), max_length=100)
    title = models.CharField(verbose_name=_('title'), max_length=300)
    email = models.CharField(verbose_name=_('email'), max_length=300)
    phone = models.CharField(verbose_name=_('phone'), max_length=50, blank=True)
    field_report = models.ForeignKey(
        FieldReport, verbose_name=_('field report'), related_name='contacts', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('field report contacts')
        verbose_name_plural = _('field report contacts')

    def __str__(self):
        return '%s: %s' % (self.name, self.title)


class ActionOrg:
    NATIONAL_SOCIETY = 'NTLS'
    FOREIGN_SOCIETY = 'PNS'
    FEDERATION = 'FDRN'

    CHOICES = (
        (NATIONAL_SOCIETY, _('National Society')),
        (FOREIGN_SOCIETY, _('Foreign Society')),
        (FEDERATION, _('Federation')),
    )


class ActionType:
    EVENT = 'EVT'
    EARLY_WARNING = 'EW'
    EPIDEMIC = 'EPI'
    COVID = 'COVID'

    CHOICES = (
        (EVENT, _('Event')),
        (EARLY_WARNING, _('Early Warning')),
        (EPIDEMIC, _('Epidemic')),
        (COVID, _('COVID-19')),
    )


class ActionCategory:
    GENERAL = 'General'
    HEALTH = 'Health'
    NS_INSTITUTIONAL_STRENGTHENING = 'NS Institutional Strengthening'
    SOCIO_ECONOMIC_IMPACTS = 'Socioeconomic Interventions'

    CHOICES = (
        (GENERAL, _('General')),
        (HEALTH, _('Health')),
        (NS_INSTITUTIONAL_STRENGTHENING, _('NS Institutional Strengthening')),
        (SOCIO_ECONOMIC_IMPACTS, _('Socioeconomic Interventions')),
    )


class Action(models.Model):
    """ Action taken """
    name = models.CharField(verbose_name=_('name'), max_length=100)
    organizations = ArrayField(
        models.CharField(choices=ActionOrg.CHOICES, max_length=4),
        verbose_name=_('organizations'), default=list, blank=True
    )
    field_report_types = ArrayField(
        models.CharField(choices=ActionType.CHOICES, max_length=16),
        verbose_name=_('field report types'), default=list,
    )
    category = models.CharField(
        max_length=255, verbose_name=_('category'), choices=ActionCategory.CHOICES, default=ActionCategory.GENERAL
    )
    is_disabled = models.BooleanField(verbose_name=_('is disabled?'), default=False, help_text=_('Disable in form'))

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')

    def __str__(self):
        return self.name


class ActionsTaken(models.Model):
    """ All the actions taken by an organization """

    organization = models.CharField(
        choices=ActionOrg.CHOICES,
        verbose_name=_('organization'), max_length=16,
    )
    actions = models.ManyToManyField(Action, verbose_name=_('actions'), blank=True)
    summary = models.TextField(verbose_name=_('summary'), blank=True)
    field_report = models.ForeignKey(
        FieldReport, verbose_name=_('field report'), related_name='actions_taken', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('actions taken')
        verbose_name_plural = _('all actions taken')

    def __str__(self):
        return '%s: %s' % (self.get_organization_display(), self.summary)


class SourceType(models.Model):
    """ Types of sources """
    name = models.CharField(verbose_name=_('name'), max_length=40)

    class Meta:
        verbose_name = _('source type')
        verbose_name_plural = _('source types')

    def __str__(self):
        return self.name


class Source(models.Model):
    """ Source of information """
    stype = models.ForeignKey(SourceType, verbose_name=_('type'), on_delete=models.PROTECT)
    spec = models.TextField(verbose_name=_('spec'), blank=True)
    field_report = models.ForeignKey(
        FieldReport, verbose_name=_('field report'), related_name='sources', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _('source')
        verbose_name_plural = _('sources')

    def __str__(self):
        return '%s: %s' % (self.stype.name, self.spec)


class Profile(models.Model):
    """ Holds location and identifying information about users """
    NTLS = 'NTLS'
    DLGN = 'DLGN'
    SCRT = 'SCRT'
    ICRC = 'ICRC'
    OTHR = 'OTHR'

    ORGANIZATION_TYPES = (
        (NTLS, _('National Society')),
        (DLGN, _('Delegation')),
        (SCRT, _('Secretariat')),
        (ICRC, _('ICRC')),
        (OTHR, _('Other')),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
        editable=False,
    )

    country = models.ForeignKey(Country, verbose_name=_('country'), null=True, on_delete=models.SET_NULL)

    # TODO org should also be discreet choices from this list
    # https://drive.google.com/drive/u/1/folders/1auXpAPhOh4YROnKxOfFy5-T7Ki96aIb6k
    org = models.CharField(verbose_name=_('organization'), blank=True, max_length=100)
    org_type = models.CharField(choices=ORGANIZATION_TYPES, verbose_name=_('organization type'), max_length=4, blank=True)
    city = models.CharField(verbose_name=_('city'), blank=True, null=True, max_length=100)
    department = models.CharField(verbose_name=_('department'), blank=True, null=True, max_length=100)
    position = models.CharField(verbose_name=_('position'), blank=True, null=True, max_length=100)
    phone_number = models.CharField(verbose_name=_('phone number'), blank=True, null=True, max_length=100)
    last_frontend_login = models.DateTimeField(verbose_name=_('last frontend login'), null=True, blank=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return self.user.username


class EmergencyOperationsBase(models.Model):
    """Common fields used by EmergencyOperations* Tables"""
    is_validated = models.BooleanField(
        verbose_name=_('is validated?'), default=False, help_text=_('Did anyone check the editable data?')
    )
    created_at = models.DateTimeField(verbose_name=_('created_at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('modified_at'), auto_now=True)

    # Raw data from the scraper
    raw_file_name = models.TextField(null=True, blank=True)
    raw_file_url = models.TextField(null=True, blank=True)
    raw_appeal_number = models.TextField(verbose_name=_('appeal number (raw)'), null=True, blank=True)
    raw_date_of_issue = models.TextField(verbose_name=_('date of issue (raw)'), null=True, blank=True)
    raw_glide_number = models.TextField(verbose_name=_('glide number (raw)'), null=True, blank=True)
    raw_num_of_people_to_be_assisted = models.TextField(
        verbose_name=_('number of people to be assisted (raw)'), null=True, blank=True)
    raw_num_of_people_affected = models.TextField(verbose_name=_('number of people affected (raw)'), null=True, blank=True)
    raw_operation_start_date = models.TextField(null=True, blank=True)
    raw_dref_allocated = models.TextField(null=True, blank=True)

    raw_disaster_risk_reduction_female = models.TextField(
        verbose_name=_('number of disaster risk reduction female (raw)'), null=True, blank=True)
    raw_disaster_risk_reduction_male = models.TextField(
        verbose_name=_('number of disaster risk reduction male (raw)'), null=True, blank=True)
    raw_disaster_risk_reduction_people_reached = models.TextField(
        verbose_name=_('number of disaster risk reduction people reached (raw)'), null=True, blank=True)
    raw_disaster_risk_reduction_people_targeted = models.TextField(
        verbose_name=_('number of disaster risk reduction people targeted (raw)'), null=True, blank=True)
    raw_disaster_risk_reduction_requirements = models.TextField(
        verbose_name=_('number of disaster risk reduction requirements (raw)'), null=True, blank=True)
    raw_health_female = models.TextField(verbose_name=_('health female (raw)'), null=True, blank=True)
    raw_health_male = models.TextField(verbose_name=_('health male (raw)'), null=True, blank=True)
    raw_health_people_reached = models.TextField(verbose_name=_('health people reached (raw)'), null=True, blank=True)
    raw_health_people_targeted = models.TextField(verbose_name=_('health people targeted (raw)'), null=True, blank=True)
    raw_health_requirements = models.TextField(verbose_name=_('health requirements (raw)'), null=True, blank=True)
    raw_livelihoods_and_basic_needs_female = models.TextField(
        verbose_name=_('number of livelihhods and basic needs female (raw)'), null=True, blank=True)
    raw_livelihoods_and_basic_needs_male = models.TextField(
        verbose_name=_('number of livelihhods and basic needs male (raw)'), null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_reached = models.TextField(
        verbose_name=_('number of livelihhods and basic needs people reached (raw)'), null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_targeted = models.TextField(
        verbose_name=_('number of livelihhods and basic needs people targeted (raw)'), null=True, blank=True)
    raw_livelihoods_and_basic_needs_requirements = models.TextField(
        verbose_name=_('number of livelihhods and basic needs requirements (raw)'), null=True, blank=True)
    raw_migration_female = models.TextField(verbose_name=_('number of migration female (raw)'), null=True, blank=True)
    raw_migration_male = models.TextField(verbose_name=_('number of migration male (raw)'), null=True, blank=True)
    raw_migration_people_reached = models.TextField(
        verbose_name=_('number of migration people reached (raw)'), null=True, blank=True)
    raw_migration_people_targeted = models.TextField(
        verbose_name=_('number of migration people targeted (raw)'), null=True, blank=True)
    raw_migration_requirements = models.TextField(verbose_name=_('number of migration requirements (raw)'), null=True, blank=True)
    raw_protection_gender_and_inclusion_female = models.TextField(
        verbose_name=_('number of protection gender and inclusion female (raw)'), null=True, blank=True)
    raw_protection_gender_and_inclusion_male = models.TextField(
        verbose_name=_('number of protection gender and inclusion male (raw)'), null=True, blank=True)
    raw_protection_gender_and_inclusion_people_reached = models.TextField(
        verbose_name=_('number of protection gender and inclusion people reached (raw)'), null=True, blank=True)
    raw_protection_gender_and_inclusion_people_targeted = models.TextField(
        verbose_name=_('number of protection gender and inclusion people targeted (raw)'), null=True, blank=True)
    raw_protection_gender_and_inclusion_requirements = models.TextField(
        verbose_name=_('number of protection gender and inclusion requirements (raw)'), null=True, blank=True)
    raw_shelter_female = models.TextField(verbose_name=_('number of shelter female (raw)'), null=True, blank=True)
    raw_shelter_male = models.TextField(verbose_name=_('number of shelter male (raw)'), null=True, blank=True)
    raw_shelter_people_reached = models.TextField(verbose_name=_('number of shelter people reached (raw)'), null=True, blank=True)
    raw_shelter_people_targeted = models.TextField(
        verbose_name=_('number of shelter people targeted (raw)'), null=True, blank=True)
    raw_shelter_requirements = models.TextField(verbose_name=_('number of shelter requirements (raw)'), null=True, blank=True)
    raw_water_sanitation_and_hygiene_female = models.TextField(
        verbose_name=_('number of water sanitation and hygiene female (raw)'), null=True, blank=True)
    raw_water_sanitation_and_hygiene_male = models.TextField(
        verbose_name=_('number of water sanitation and hygiene male (raw)'), null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_reached = models.TextField(
        verbose_name=_('number of water sanitation and hygiene people reached (raw)'), null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_targeted = models.TextField(
        verbose_name=_('number of water sanitation and hygiene people targeted (raw)'), null=True, blank=True)
    raw_water_sanitation_and_hygiene_requirements = models.TextField(
        verbose_name=_('number of water sanitation and hygiene requirements (raw)'), null=True, blank=True)

    # Fields for the cleaned data
    file_name = models.CharField(max_length=200, null=True, blank=True)
    appeal_number = models.CharField(verbose_name=_('appeal number'), max_length=20, null=True, blank=True)
    date_of_issue = models.DateField(verbose_name=_('date of issue'), null=True, blank=True)
    glide_number = models.CharField(verbose_name=_('glide number'), max_length=18, null=True, blank=True)
    num_of_people_affected = models.IntegerField(verbose_name=_('number of people affected'), null=True, blank=True)
    num_of_people_to_be_assisted = models.IntegerField(verbose_name=_('number of people to be assisted'), null=True, blank=True)
    operation_start_date = models.DateField(verbose_name=_('operation start date'), null=True, blank=True)

    dref_allocated = models.IntegerField(verbose_name=_('DREF allocated'), null=True, blank=True)
    disaster_risk_reduction_female = models.IntegerField(
        verbose_name=_('number of disaster risk reduction female'), null=True, blank=True)
    disaster_risk_reduction_male = models.IntegerField(
        verbose_name=_('number of disaster risk reduction male'), null=True, blank=True)
    disaster_risk_reduction_people_reached = models.IntegerField(
        verbose_name=_('number of disaster risk reduction people reached'), null=True, blank=True)
    disaster_risk_reduction_people_targeted = models.IntegerField(
        verbose_name=_('number of disaster risk reduction people targeted'), null=True, blank=True)
    disaster_risk_reduction_requirements = models.IntegerField(
        verbose_name=_('number of disaster risk reduction people requirements'), null=True, blank=True)
    health_female = models.IntegerField(verbose_name=_('number of health female'), null=True, blank=True)
    health_male = models.IntegerField(verbose_name=_('number of health male'), null=True, blank=True)
    health_people_reached = models.IntegerField(verbose_name=_('number of health people reached'), null=True, blank=True)
    health_people_targeted = models.IntegerField(verbose_name=_('number of health people targeted'), null=True, blank=True)
    health_requirements = models.IntegerField(verbose_name=_('number of health requirements'), null=True, blank=True)
    livelihoods_and_basic_needs_female = models.IntegerField(
        verbose_name=_('number of livelihhods and basic needs female'), null=True, blank=True)
    livelihoods_and_basic_needs_male = models.IntegerField(
        verbose_name=_('number of livelihhods and basic needs male'), null=True, blank=True)
    livelihoods_and_basic_needs_people_reached = models.IntegerField(
        verbose_name=_('number of livelihhods and basic people reached'), null=True, blank=True)
    livelihoods_and_basic_needs_people_targeted = models.IntegerField(
        verbose_name=_('number of livelihhods and basic people targeted'), null=True, blank=True)
    livelihoods_and_basic_needs_requirements = models.IntegerField(
        verbose_name=_('number of livelihhods and basic needs requirements'), null=True, blank=True)
    migration_female = models.IntegerField(verbose_name=_('number of migration female'), null=True, blank=True)
    migration_male = models.IntegerField(verbose_name=_('number of migration male'), null=True, blank=True)
    migration_people_reached = models.IntegerField(verbose_name=_('number of migration people reached'), null=True, blank=True)
    migration_people_targeted = models.IntegerField(verbose_name=_('number of migration people targeted'), null=True, blank=True)
    migration_requirements = models.IntegerField(verbose_name=_('number of migration requirements'), null=True, blank=True)
    protection_gender_and_inclusion_female = models.IntegerField(
        verbose_name=_('number of protection gender and inclusion female'), null=True, blank=True)
    protection_gender_and_inclusion_male = models.IntegerField(
        verbose_name=_('number of protection gender and inclusion male'), null=True, blank=True)
    protection_gender_and_inclusion_people_reached = models.IntegerField(
        verbose_name=_('number of protection gender and inclusion people reached'), null=True, blank=True)
    protection_gender_and_inclusion_people_targeted = models.IntegerField(
        verbose_name=_('number of protection gender and inclusion people targeted'), null=True, blank=True)
    protection_gender_and_inclusion_requirements = models.IntegerField(
        verbose_name=_('number of protection gender and inclusion requirements'), null=True, blank=True)
    shelter_female = models.IntegerField(verbose_name=_('number of shelter female'), null=True, blank=True)
    shelter_male = models.IntegerField(verbose_name=_('number of shelter male'), null=True, blank=True)
    shelter_people_reached = models.IntegerField(verbose_name=_('number of shelter people reached'), null=True, blank=True)
    shelter_people_targeted = models.IntegerField(verbose_name=_('number of shelter people targeted'), null=True, blank=True)
    shelter_requirements = models.IntegerField(verbose_name=_('number of shelter people requirements'), null=True, blank=True)
    water_sanitation_and_hygiene_female = models.IntegerField(
        verbose_name=_('water sanitation and hygiene female'), null=True, blank=True)
    water_sanitation_and_hygiene_male = models.IntegerField(
        verbose_name=_('water sanitation and hygiene male'), null=True, blank=True)
    water_sanitation_and_hygiene_people_reached = models.IntegerField(
        verbose_name=_('water sanitation and hygiene people reached'), null=True, blank=True)
    water_sanitation_and_hygiene_people_targeted = models.IntegerField(
        verbose_name=_('water sanitation and hygiene people targeted'), null=True, blank=True)
    water_sanitation_and_hygiene_requirements = models.IntegerField(
        verbose_name=_('water sanitation and hygiene requirements'), null=True, blank=True)

    class Meta:
        abstract = True


class EmergencyOperationsDataset(EmergencyOperationsBase):
    # Raw data from the scraper
    raw_appeal_launch_date = models.TextField(verbose_name=_('appeal launch date (raw)'), null=True, blank=True)
    raw_category_allocated = models.TextField(verbose_name=_('category allocated (raw)'), null=True, blank=True)
    raw_expected_end_date = models.TextField(verbose_name=_('expected end date (raw)'), null=True, blank=True)
    raw_expected_time_frame = models.TextField(verbose_name=_('expected time frame (raw)'), null=True, blank=True)

    raw_education_female = models.TextField(verbose_name=_('number of eduction female (raw)'), null=True, blank=True)
    raw_education_male = models.TextField(verbose_name=_('number of eduction male (raw)'), null=True, blank=True)
    raw_education_people_reached = models.TextField(
        verbose_name=_('number of eduction people reached (raw)'), null=True, blank=True)
    raw_education_people_targeted = models.TextField(
        verbose_name=_('number of eduction people targeted (raw)'), null=True, blank=True)
    raw_education_requirements = models.TextField(verbose_name=_('number of eduction requirements (raw)'), null=True, blank=True)

    # Raw: Remove fields from mixin
    raw_operation_start_date = None

    # Fields for the cleaned data
    appeal_launch_date = models.DateField(verbose_name=_('appeal launch date'), null=True, blank=True)
    category_allocated = models.CharField(verbose_name=_('category allocated'), max_length=100, null=True, blank=True)
    expected_end_date = models.DateField(verbose_name=_('expected end date'), null=True, blank=True)
    expected_time_frame = models.IntegerField(verbose_name=_('expected time frame'), null=True, blank=True)

    education_female = models.IntegerField(verbose_name=_('number of eduction female'), null=True, blank=True)
    education_male = models.IntegerField(verbose_name=_('number of eduction male'), null=True, blank=True)
    education_people_reached = models.IntegerField(verbose_name=_('number of eduction people reached'), null=True, blank=True)
    education_people_targeted = models.IntegerField(verbose_name=_('number of eduction people targeted'), null=True, blank=True)
    education_requirements = models.IntegerField(verbose_name=_('number of eduction requirements'), null=True, blank=True)

    # Clean data: Remove fields from mixin
    operation_start_date = None

    class Meta:
        verbose_name = _('emergency operations dataset')
        verbose_name_plural = _('emergency operations datasets')

    def __str__(self):
        return self.raw_file_name


class EmergencyOperationsPeopleReached(EmergencyOperationsBase):
    # Raw data from the scraper
    raw_epoa_update_num = models.TextField(verbose_name=_('EPOA update number (raw)'), null=True, blank=True)
    raw_operation_timeframe = models.TextField(verbose_name=_('operation timeframe (raw)'), null=True, blank=True)
    raw_time_frame_covered_by_update = models.TextField(
        verbose_name=_('time frame covered by update (raw)'), null=True, blank=True)

    # Raw: Remove fields from mixin
    raw_dref_allocated = None
    raw_num_of_people_affected = None
    raw_num_of_people_to_be_assisted = None
    raw_disaster_risk_reduction_people_targeted = None
    raw_health_people_targeted = None
    raw_livelihoods_and_basic_needs_people_targeted = None
    raw_migration_people_targeted = None
    raw_protection_gender_and_inclusion_people_targeted = None
    raw_shelter_people_targeted = None
    raw_water_sanitation_and_hygiene_people_targeted = None

    # Fields for the cleaned data
    epoa_update_num = models.IntegerField(verbose_name=_('EPOA update number'), null=True, blank=True)
    operation_timeframe = models.CharField(verbose_name=_('operation timeframe'), max_length=200, null=True, blank=True)
    time_frame_covered_by_update = models.CharField(
        verbose_name=_('time frame covered by update'), max_length=200, null=True, blank=True)

    # Clean data: Remove fields from mixin
    dref_allocated = None
    num_of_people_affected = None
    num_of_people_to_be_assisted = None
    disaster_risk_reduction_people_targeted = None
    health_people_targeted = None
    livelihoods_and_basic_needs_people_targeted = None
    migration_people_targeted = None
    protection_gender_and_inclusion_people_targeted = None
    shelter_people_targeted = None
    water_sanitation_and_hygiene_people_targeted = None

    class Meta:
        verbose_name = _('emergency operations people reached')
        verbose_name_plural = _('emergency operations people reached')

    def __str__(self):
        return self.raw_file_name


class EmergencyOperationsEA(EmergencyOperationsBase):
    raw_appeal_ends = models.TextField(verbose_name=_('appeal ends (raw)'), null=True, blank=True)
    raw_appeal_launch_date = models.TextField(verbose_name=_('appeal launch date (raw)'), null=True, blank=True)
    raw_current_operation_budget = models.TextField(verbose_name=_('current operation budget (raw)'), null=True, blank=True)

    # Raw: Remove fields from mixin
    raw_date_of_issue = None
    raw_num_of_people_affected = None
    raw_operation_start_date = None

    # Fields for the cleaned data
    appeal_ends = models.DateField(verbose_name=_('appeal ends'), null=True, blank=True)
    appeal_launch_date = models.DateField(verbose_name=_('appeal launch date'), null=True, blank=True)
    current_operation_budget = models.IntegerField(verbose_name=_('current operation budget'), null=True, blank=True)

    # Clean data: Remove fields from mixin
    date_of_issue = None
    num_of_people_affected = None
    operation_start_date = None

    class Meta:
        verbose_name = _('emergency operations emergency appeal')
        verbose_name_plural = _('emergency operations emergency appeals')

    def __str__(self):
        return self.raw_file_name


class EmergencyOperationsFR(EmergencyOperationsBase):
    raw_date_of_disaster = models.TextField(verbose_name=_('date of disaster (raw)'), null=True, blank=True)
    raw_num_of_other_partner_involved = models.TextField(
        verbose_name=_('number of other partner involved (raw)'), null=True, blank=True)
    raw_num_of_partner_ns_involved = models.TextField(
        verbose_name=_('number of NS partner involved (raw)'), null=True, blank=True)
    raw_operation_end_date = models.TextField(verbose_name=_('operation end date (raw)'), null=True, blank=True)
    raw_overall_operation_budget = models.TextField(verbose_name=_('overall operation budget (raw)'), null=True, blank=True)

    # Raw: Remove fields from mixin
    raw_dref_allocated = None
    raw_disaster_risk_reduction_people_targeted = None
    raw_health_people_targeted = None
    raw_livelihoods_and_basic_needs_people_targeted = None
    raw_migration_people_targeted = None
    raw_protection_gender_and_inclusion_people_targeted = None
    raw_shelter_people_targeted = None
    raw_water_sanitation_and_hygiene_people_targeted = None

    # Fields for the cleaned data
    date_of_disaster = models.DateField(verbose_name=_('date of disaster'), null=True, blank=True)
    num_of_other_partner_involved = models.TextField(verbose_name=_('number of other partner involved'), null=True, blank=True)
    num_of_partner_ns_involved = models.TextField(verbose_name=_('number of NS partner involved'), null=True, blank=True)
    operation_end_date = models.DateField(verbose_name=_('operation end date'), null=True, blank=True)
    operation_start_date = models.DateField(verbose_name=_('operation start date'), null=True, blank=True)
    overall_operation_budget = models.IntegerField(verbose_name=_('overall operation budget'), null=True, blank=True)

    # Clean data: Remove fields from mixin
    dref_allocated = None
    disaster_risk_reduction_people_targeted = None
    health_people_targeted = None
    livelihoods_and_basic_needs_people_targeted = None
    migration_people_targeted = None
    protection_gender_and_inclusion_people_targeted = None
    shelter_people_targeted = None
    water_sanitation_and_hygiene_people_targeted = None

    class Meta:
        verbose_name = _('emergency operations final report')
        verbose_name_plural = _('emergency operations final reports')

    def __str__(self):
        return self.raw_file_name


class CronJobStatus(IntEnum):
    NEVER_RUN = -1
    SUCCESSFUL = 0
    WARNED = 1
    ERRONEOUS = 2

    # class Labels:
    #     NEVER_RUN = _('Never run')
    #     SUCCESSFUL = _('Successfull')
    #     WARNED = _('Warned')
    #     ERRONEOUS = _('Erroneous')


class CronJob(models.Model):
    """ CronJob log row about jobs results """
    name = models.CharField(verbose_name=_('name'), max_length=100, default='')
    status = EnumIntegerField(CronJobStatus, verbose_name=_('status'), default=-1)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    message = models.TextField(verbose_name=_('message'), null=True, blank=True)
    num_result = models.IntegerField(verbose_name=_('number of results'), default=0)
    storing_days = models.IntegerField(verbose_name=_('storing days'), default=3)
    backend_side = models.BooleanField(
        verbose_name=_('backend side'), default=True,
    )  # We could keep backend/frontend ingest results here also

    class Meta:
        verbose_name = _('cronjob log record')
        verbose_name_plural = _('cronjob log records')

    def __str__(self):
        if self.num_result:
            return '%s | %s : %s | %s' % (self.name, str(self.status.label), str(self.num_result), str(self.created_at)[5:16])
        else:
            return '%s | %s | %s' % (self.name, str(self.status.label), str(self.created_at)[5:16])  # omit irrelevant 0

    # Given a request containing new CronJob log row, validate and add the CronJob log row.
    def sync_cron(body):
        new = []
        errors = []
        fields = {'name': body['name'], 'message': body['message']}
        error = None

        status = int(body['status'])
        if status in [CronJobStatus.SUCCESSFUL, CronJobStatus.WARNED, CronJobStatus.ERRONEOUS]:
            fields['status'] = status
        else:
            error = 'Status is not valid',

        if 'num_result' in body:
            if body['num_result'] >= 0:
                fields['num_result'] = body['num_result']
            else:
                error = 'Num_result is not valid',

        if 'storing_days' in body:
            if body['storing_days'] > 0:
                fields['storing_days'] = body['storing_days']
                store_me = body['storing_days']
            else:
                error = 'Storing_days is not valid',
        else:
            store_me = 3  # default storing days

        if 'backend_side' in body:
            fields['backend_side'] = True if body['backend_side'] else False

        if error is not None:
            errors.append({
                'error': error,
                'record': body,
            })
        else:
            new.append(CronJob(**fields))

        if not len(errors):
            CronJob.objects.filter(
                name=body['name'], created_at__lt=datetime.now(
                    pytz.timezone('UTC')) - timedelta(days=store_me)
            ).delete()  # Delete old ones, "log-rotate"
            CronJob.objects.bulk_create(new)

        return errors, new

# To find related scripts from go-api root dir:
# grep -rl CronJob --exclude-dir=__pycache__ --exclude-dir=main --exclude-dir=migrations --exclude=CHANGELOG.md *


class AuthLog(models.Model):
    action = models.CharField(verbose_name=_('action'), max_length=64)
    username = models.CharField(verbose_name=_('username'), max_length=256, null=True)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    # ip = models.GenericIPAddressField(verbose_name=_('IP'), null=True)

    class Meta:
        verbose_name = _('auth log')
        verbose_name_plural = _('auth logs')

    def __unicode__(self):
        return '{0} - {1}'.format(self.action, self.username)

    def __str__(self):
        return '{0} - {1}'.format(self.action, self.username)


class ReversionDifferenceLog(models.Model):
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    action = models.CharField(verbose_name=_('action'), max_length=64)  # Added, Changed, etc
    username = models.CharField(verbose_name=_('username'), max_length=256, null=True)
    object_id = models.CharField(verbose_name=_('object id'), max_length=191, blank=True)
    object_name = models.TextField(verbose_name=_('object name'), null=True, blank=True)  # the name of the record
    object_type = models.CharField(verbose_name=_('object type'), max_length=50, blank=True)  # Emergency, Appeal, etc
    changed_from = ArrayField(
        models.TextField(null=True, blank=True),
        verbose_name=_('changed from'), default=list, null=True, blank=True
    )
    changed_to = ArrayField(
        models.TextField(null=True, blank=True),
        verbose_name=_('changed to'), default=list, null=True, blank=True
    )

    class Meta:
        verbose_name = _('reversion difference log')
        verbose_name_plural = _('reversion difference logs')

    def __unicode__(self):
        return '{0} - {1} - {2} - {3}'.format(self.username, self.action, self.object_type, self.object_id)

    def __str__(self):
        return '{0} - {1} - {2} - {3}'.format(self.username, self.action, self.object_type, self.object_id)


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    # ip = request.META.get('REMOTE_ADDR')
    if user:
        AuthLog.objects.create(action='user_logged_in', username=user.username)


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    # ip = request.META.get('REMOTE_ADDR')
    if user:
        AuthLog.objects.create(action='user_logged_out', username=user.username)


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    AuthLog.objects.create(action='user_login_failed', username=credentials.get('username', None))


from .triggers import *  # noqa: E402 F403 F401
