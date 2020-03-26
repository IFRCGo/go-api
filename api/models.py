from django.db import models
from django.conf import settings
from django.utils import timezone
from enumfields import IntEnum, EnumIntegerField, EnumField
from .storage import AzureStorage
from tinymce import HTMLField
from django.core.validators import FileExtensionValidator, validate_slug
from django.contrib.postgres.fields import ArrayField
from datetime import datetime, timedelta
import pytz
from .utils import validate_slug_number

# Write model properties to dictionary
def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values())
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class DisasterType(models.Model):
    """ summary of disaster """
    name = models.CharField(max_length=100)
    summary = models.TextField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class RegionName(IntEnum):
    AFRICA = 0
    AMERICAS = 1
    ASIA_PACIFIC = 2
    EUROPE = 3
    MENA = 4


class Region(models.Model):
    """ A region """
    name = EnumIntegerField(RegionName)

    def indexing(self):
        return {
            'id': self.id,
            'event_id': None,
            'type': 'region',
            'name': ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'Middle East North Africa'][self.name],
            'keyword': None,
            'body': ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'Middle East North Africa'][self.name],
            'date': None
        }

    def es_id(self):
        return 'region-%s' % self.id

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'MENA'][self.name]

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

    # select name, society_name, record_type from api_country where name like '%luster%';
    # select name, society_name, record_type from api_country where name like '%egion%';
    # select name, society_name, record_type from api_country where name like '%ffice%'; -- no result
    # update api_country set record_type=2 where name like '%luster%';
    # update api_country set record_type=3 where name like '%egion%';


class Country(models.Model):
    """ A country """

    name = models.CharField(max_length=100)
    record_type = EnumIntegerField(CountryType, default=1, help_text='Type of entity')
    iso = models.CharField(max_length=2, null=True)
    iso3 = models.CharField(max_length=3, null=True)
    society_name = models.TextField(blank=True)
    society_url = models.URLField(blank=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    overview = models.TextField(blank=True, null=True)
    key_priorities = models.TextField(blank=True, null=True)
    inform_score = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=3)
    # logo = models.FileField(blank=True, null=True, upload_to='documents/', # for local tests
    logo = models.FileField(
        blank=True, null=True, upload_to=logo_document_path,
        storage=AzureStorage(), validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'gif'])]
    )

    # Population Data From WB API
    wb_population = models.PositiveIntegerField(null=True, blank=True, help_text='Population data from WB API')
    wb_year = models.CharField(max_length=4, null=True, blank=True, help_text='Population data year from WB API')

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
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class District(models.Model):
    """ Admin level 1 field """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    country_iso = models.CharField(max_length=3, null=True)
    country_name = models.CharField(max_length=100)
    is_enclave = models.BooleanField(default=False, help_text='Is it an enclave away from parent country?') # used to mark if the district is far away from the country

    # Population Data From WB API
    wb_population = models.PositiveIntegerField(null=True, blank=True, help_text='Population data from WB API')
    wb_year = models.CharField(max_length=4, null=True, blank=True, help_text='Population data year from WB API')

    class Meta:
        ordering = ('code',)

    def __str__(self):
        return '%s - %s' % (self.country_name, self.name)


class VisibilityChoices(IntEnum):
    MEMBERSHIP = 1
    IFRC = 2
    PUBLIC = 3


# Common parent class for key figures.
# Country/region variants inherit from this.
class AdminKeyFigure(models.Model):
    figure = models.CharField(max_length=100)
    deck = models.CharField(max_length=50)
    source = models.CharField(max_length=256)
    visibility = EnumIntegerField(VisibilityChoices, default=3)
    class Meta:
        ordering = ('source',)
    def __str__(self):
        return self.source

class RegionKeyFigure(AdminKeyFigure):
    region = models.ForeignKey(Region, related_name='key_figures', on_delete=models.CASCADE)

class CountryKeyFigure(AdminKeyFigure):
    country = models.ForeignKey(Country, related_name='key_figures', on_delete=models.CASCADE)

class PositionType(IntEnum):
    TOP = 1
    HIGH = 2
    MIDDLE = 3
    LOW = 4
    BOTTOM = 5

class RegionSnippet(models.Model):
    region = models.ForeignKey(Region, related_name='snippets', on_delete=models.CASCADE)
    snippet = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to='regions/%Y/%m/%d/', storage=AzureStorage())
    visibility = EnumIntegerField(VisibilityChoices, default=3)
    position = EnumIntegerField(PositionType, default=3)
    class Meta:
        ordering = ('position', 'id',)

class CountrySnippet(models.Model):
    country = models.ForeignKey(Country, related_name='snippets', on_delete=models.CASCADE)
    snippet = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to='countries/%Y/%m/%d/', storage=AzureStorage())
    visibility = EnumIntegerField(VisibilityChoices, default=3)
    position = EnumIntegerField(PositionType, default=3)
    class Meta:
        ordering = ('position', 'id',)

class AdminLink(models.Model):
    title = models.CharField(max_length=100)
    url = models.URLField(max_length=300)

class RegionLink(AdminLink):
    region = models.ForeignKey(Region, related_name='links', on_delete=models.CASCADE)

class CountryLink(AdminLink):
    country = models.ForeignKey(Country, related_name='links', on_delete=models.CASCADE)


class AdminContact(models.Model):
    ctype = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    email = models.CharField(max_length=300)

class RegionContact(AdminContact):
    region = models.ForeignKey(Region, related_name='contacts', on_delete=models.CASCADE)

class CountryContact(AdminContact):
    country = models.ForeignKey(Country, related_name='contacts', on_delete=models.CASCADE)


class AlertLevel(IntEnum):
    GREEN = 0
    ORANGE = 1
    RED = 2


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=50, default=None, unique=True, null=True, blank=True, validators=[validate_slug, validate_slug_number], help_text='Optional string for a clean URL. For example, go.ifrc.org/emergencies/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.')
    dtype = models.ForeignKey(DisasterType, null=True, on_delete=models.SET_NULL)
    districts = models.ManyToManyField(District, blank=True)
    countries = models.ManyToManyField(Country)
    regions = models.ManyToManyField(Region)
    parent_event = models.ForeignKey('self', null=True, blank=True, verbose_name='Parent Emergency', on_delete=models.SET_NULL)
    summary = HTMLField(blank=True, default='')

    num_injured = models.IntegerField(null=True, blank=True)
    num_dead = models.IntegerField(null=True, blank=True)
    num_missing = models.IntegerField(null=True, blank=True)
    num_affected = models.IntegerField(null=True, blank=True)
    num_displaced = models.IntegerField(null=True, blank=True)

    ifrc_severity_level = EnumIntegerField(AlertLevel, default=0, verbose_name='IFRC Severity level') # Changed to ‘IFRC Severity level’ from alert_level - Sune's ask
    glide = models.CharField(max_length=18, blank=True)

    disaster_start_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    previous_update = models.DateTimeField(null=True, blank=True)

    auto_generated = models.BooleanField(default=False, editable=False)
    auto_generated_source = models.CharField(max_length=50, null=True, blank=True, editable=False)

    # Meant to give the organization a way of highlighting certain, important events.
    is_featured = models.BooleanField(default=False, verbose_name='Is Featured on Home Page')

    # Allows admins to feature the Event on the region page.
    is_featured_region = models.BooleanField(default=False, verbose_name='Is Featured on Region Page')

    hide_attached_field_reports = models.BooleanField(default=False)

    class Meta:
        ordering = ('-disaster_start_date',)
        verbose_name = 'Emergency'
        verbose_name_plural = 'Emergencies'

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

    ctype = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    email = models.CharField(max_length=300)
    phone = models.CharField(max_length=100, blank=True, null=True)
    event = models.ForeignKey(Event, related_name='contacts', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.name, self.title)


class KeyFigure(models.Model):
    event = models.ForeignKey(Event, related_name='key_figures', on_delete=models.CASCADE)
    # key figure metric
    number = models.CharField(max_length=100)
    # key figure units
    deck = models.CharField(max_length=50)
    # key figure website link, publication
    source = models.CharField(max_length=256)


def snippet_image_path(instance, filename):
    return 'emergencies/%s/%s' % (instance.event.id, filename)

class Snippet(models.Model):
    """ Snippet of text """
    snippet = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=snippet_image_path, storage=AzureStorage())
    event = models.ForeignKey(Event, related_name='snippets', on_delete=models.CASCADE)
    visibility = EnumIntegerField(VisibilityChoices, default=3)
    position = EnumIntegerField(PositionType, default=3)
    class Meta:
        ordering = ('position', 'id',)

class SituationReportType(models.Model):
    """ Document type, to be able to filter Situation Reports """
    type = models.CharField(max_length=50)
    def __str__(self):
        return self.type


def sitrep_document_path(instance, filename):
    return 'sitreps/%s/%s' % (instance.event.id, filename)


class SituationReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    document = models.FileField(null=True, blank=True, upload_to=sitrep_document_path, storage=AzureStorage())
    document_url = models.URLField(blank=True)

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    type = models.ForeignKey(SituationReportType, related_name='situation_reports', null=True, on_delete=models.SET_NULL)
    visibility = EnumIntegerField(VisibilityChoices, default=VisibilityChoices.MEMBERSHIP)

    def __str__(self):
        return '%s - %s' % (self.event, self.name)


class GDACSEvent(models.Model):
    """ A GDACS type event, from alerts """

    eventid = models.CharField(max_length=12)
    title = models.TextField()
    description = models.TextField()
    image = models.URLField(null=True)
    report = models.URLField(null=True)
    publication_date = models.DateTimeField()
    year = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    event_type = models.CharField(max_length=16)
    alert_level = EnumIntegerField(AlertLevel, default=0)
    alert_score = models.CharField(max_length=16, null=True)
    severity = models.TextField()
    severity_unit = models.CharField(max_length=16)
    severity_value = models.CharField(max_length=16)
    population_unit = models.CharField(max_length=16)
    population_value = models.CharField(max_length=16)
    vulnerability = models.FloatField()
    countries = models.ManyToManyField(Country)
    country_text = models.TextField()

    def __str__(self):
        return self.title


class AppealType(IntEnum):
    """ summarys of appeals """
    DREF = 0
    APPEAL = 1
    INTL = 2


class AppealStatus(IntEnum):
    ACTIVE = 0
    CLOSED = 1
    FROZEN = 2
    ARCHIVED = 3


class Appeal(models.Model):
    """ An appeal for a disaster and country, containing documents """

    # appeal ID, assinged by creator
    aid = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    dtype = models.ForeignKey(DisasterType, null=True, on_delete=models.SET_NULL)
    atype = EnumIntegerField(AppealType, default=0)

    status = EnumIntegerField(AppealStatus, default=0)
    code = models.CharField(max_length=20, null=True, unique=True)
    sector = models.CharField(max_length=100, blank=True)

    num_beneficiaries = models.IntegerField(default=0)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_funded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    previous_update = models.DateTimeField(null=True, blank=True)
    real_data_update = models.DateTimeField(null=True, blank=True)

    event = models.ForeignKey(Event, related_name='appeals', null=True, blank=True, on_delete=models.SET_NULL)
    needs_confirmation = models.BooleanField(default=False)
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)

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

    def indexing(self):
        return {
            'id': self.id,
            'event_id': self.event.id if self.event is not None else None,
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
        data['atype'] = ['DREF', 'Emergency Appeal', 'International Appeal'][self.atype]
        data['country'] = self.country.name
        return data

    def __str__(self):
        return self.code


def appeal_document_path(instance, filename):
    return 'appeals/%s/%s' % (instance.appeal, filename)


class AppealDocument(models.Model):
    # Don't set `auto_now_add` so we can modify it on save
    created_at = models.DateTimeField()
    name = models.CharField(max_length=100)
    document = models.FileField(null=True, blank=True, upload_to=appeal_document_path, storage=AzureStorage())
    document_url = models.URLField(blank=True)

    appeal = models.ForeignKey(Appeal, on_delete=models.CASCADE)

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


class FieldReport(models.Model):
    """ A field report for a disaster and country, containing documents """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='user',
                             null=True,
                             blank=True,
                             on_delete=models.SET_NULL)

    # Used to differentiate reports that have and have not been synced from DMIS
    rid = models.CharField(max_length=100, null=True, blank=True, editable=False)
    summary = models.TextField(blank=True)
    description = HTMLField(blank=True, default='')
    dtype = models.ForeignKey(DisasterType, on_delete=models.PROTECT)
    event = models.ForeignKey(Event, related_name='field_reports', null=True, blank=True, on_delete=models.SET_NULL)
    districts = models.ManyToManyField(District, blank=True)
    countries = models.ManyToManyField(Country)
    regions = models.ManyToManyField(Region, blank=True)
    status = models.IntegerField(default=0)
    request_assistance = models.BooleanField(default=False)
    ns_request_assistance = models.BooleanField(default=False)

    num_injured = models.IntegerField(null=True, blank=True)
    num_dead = models.IntegerField(null=True, blank=True)
    num_missing = models.IntegerField(null=True, blank=True)
    num_affected = models.IntegerField(null=True, blank=True)
    num_displaced = models.IntegerField(null=True, blank=True)
    num_assisted = models.IntegerField(null=True, blank=True)
    num_localstaff = models.IntegerField(null=True, blank=True)
    num_volunteers = models.IntegerField(null=True, blank=True)
    num_expats_delegates = models.IntegerField(null=True, blank=True)

    #Early Warning fields
    num_potentially_affected = models.IntegerField(null=True, blank=True)
    num_highest_risk = models.IntegerField(null=True, blank=True)
    affected_pop_centres = models.CharField(max_length=512, blank=True, null=True)

    gov_num_injured = models.IntegerField(null=True, blank=True)
    gov_num_dead = models.IntegerField(null=True, blank=True)
    gov_num_missing = models.IntegerField(null=True, blank=True)
    gov_num_affected = models.IntegerField(null=True, blank=True)
    gov_num_displaced = models.IntegerField(null=True, blank=True)
    gov_num_assisted = models.IntegerField(null=True, blank=True)

    #Early Warning fields
    gov_num_potentially_affected = models.IntegerField(null=True, blank=True)
    gov_num_highest_risk = models.IntegerField(null=True, blank=True)
    gov_affected_pop_centres = models.CharField(max_length=512, blank=True, null=True)

    other_num_injured = models.IntegerField(null=True, blank=True)
    other_num_dead = models.IntegerField(null=True, blank=True)
    other_num_missing = models.IntegerField(null=True, blank=True)
    other_num_affected = models.IntegerField(null=True, blank=True)
    other_num_displaced = models.IntegerField(null=True, blank=True)
    other_num_assisted = models.IntegerField(null=True, blank=True)

    #Early Warning fields
    other_num_potentially_affected = models.IntegerField(null=True, blank=True)
    other_num_highest_risk = models.IntegerField(null=True, blank=True)
    other_affected_pop_centres = models.CharField(max_length=512, blank=True, null=True)

    # Text field for users to specify sources for where they have marked 'Other' as source.
    other_sources = models.TextField(blank=True, default='')

    # actions taken
    actions_others = models.TextField(null=True, blank=True)

    # visibility
    visibility = EnumIntegerField(VisibilityChoices, default=1)

    # information
    bulletin = EnumIntegerField(RequestChoices, default=0)
    dref = EnumIntegerField(RequestChoices, default=0)
    dref_amount = models.IntegerField(null=True, blank=True)
    appeal = EnumIntegerField(RequestChoices, default=0)
    appeal_amount = models.IntegerField(null=True, blank=True)
    imminent_dref = EnumIntegerField(RequestChoices, default=0) #only EW
    imminent_dref_amount = models.IntegerField(null=True, blank=True) #only EW
    forecast_based_action = EnumIntegerField(RequestChoices, default=0) #only EW
    forecast_based_action_amount = models.IntegerField(null=True, blank=True) #only EW

    # disaster response
    rdrt = EnumIntegerField(RequestChoices, default=0)
    num_rdrt = models.IntegerField(null=True, blank=True)
    fact = EnumIntegerField(RequestChoices, default=0)
    num_fact = models.IntegerField(null=True, blank=True)
    ifrc_staff = EnumIntegerField(RequestChoices, default=0)
    num_ifrc_staff = models.IntegerField(null=True, blank=True)

    # ERU units
    eru_base_camp = EnumIntegerField(RequestChoices, default=0)
    eru_base_camp_units = models.IntegerField(null=True, blank=True)

    eru_basic_health_care = EnumIntegerField(RequestChoices, default=0)
    eru_basic_health_care_units = models.IntegerField(null=True, blank=True)

    eru_it_telecom = EnumIntegerField(RequestChoices, default=0)
    eru_it_telecom_units = models.IntegerField(null=True, blank=True)

    eru_logistics = EnumIntegerField(RequestChoices, default=0)
    eru_logistics_units = models.IntegerField(null=True, blank=True)

    eru_deployment_hospital = EnumIntegerField(RequestChoices, default=0)
    eru_deployment_hospital_units = models.IntegerField(null=True, blank=True)

    eru_referral_hospital = EnumIntegerField(RequestChoices, default=0)
    eru_referral_hospital_units = models.IntegerField(null=True, blank=True)

    eru_relief = EnumIntegerField(RequestChoices, default=0)
    eru_relief_units = models.IntegerField(null=True, blank=True)

    eru_water_sanitation_15 = EnumIntegerField(RequestChoices, default=0)
    eru_water_sanitation_15_units = models.IntegerField(null=True, blank=True)

    eru_water_sanitation_40 = EnumIntegerField(RequestChoices, default=0)
    eru_water_sanitation_40_units = models.IntegerField(null=True, blank=True)

    eru_water_sanitation_20 = EnumIntegerField(RequestChoices, default=0)
    eru_water_sanitation_20_units = models.IntegerField(null=True, blank=True)

    # start_date is now what the user explicitly sets while filling the Field Report form.
    start_date = models.DateTimeField(blank=True, null=True)

    # Created, updated at correspond to when the report entered this system.
    # Report date is when historical reports were created.
    # For reports that are not historical, it will be equal to created_at.
    report_date = models.DateTimeField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    previous_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at', '-updated_at',)

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
            'event_id': getattr(self, 'event.id', None),
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

    ctype = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    email = models.CharField(max_length=300)
    phone = models.CharField(max_length=50, blank=True)
    field_report = models.ForeignKey(FieldReport, related_name='contacts', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.name, self.title)

class ActionOrg:
    NATIONAL_SOCIETY = 'NTLS'
    FOREIGN_SOCIETY = 'PNS'
    FEDERATION = 'FDRN'

    CHOICES = (
        (NATIONAL_SOCIETY, 'National Society'),
        (FOREIGN_SOCIETY, 'Foreign Society'),
        (FEDERATION, 'Federation'),
    )


class ActionType:
    EVENT = 'EVT'
    EARLY_WARNING = 'EW'

    CHOICES = (
        (EVENT, 'Event'),
        (EARLY_WARNING, 'Early Warning'),
    )

class Action(models.Model):
    """ Action taken """
    name = models.CharField(max_length=100)
    organizations = ArrayField(
        models.CharField(choices=ActionOrg.CHOICES, max_length=4),
        default=list, blank=True
    )
    field_report_types = ArrayField(
        models.CharField(
            choices=ActionType.CHOICES,
            max_length=4
        ),
        #default=[ActionType.EVENT]
        default=list
    )

    def __str__(self):
        return self.name


class ActionsTaken(models.Model):
    """ All the actions taken by an organization """

    organization = models.CharField(
        choices=ActionOrg.CHOICES,
        max_length=4,
    )
    actions = models.ManyToManyField(Action)
    summary = models.TextField(blank=True)
    field_report = models.ForeignKey(FieldReport, related_name='actions_taken', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.organization, self.summary)


class SourceType(models.Model):
    """ Types of sources """
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class Source(models.Model):
    """ Source of information """
    stype = models.ForeignKey(SourceType, on_delete=models.PROTECT)
    spec = models.TextField(blank=True)
    field_report = models.ForeignKey(FieldReport, related_name='sources', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.stype.name, self.spec)


class Profile(models.Model):
    """ Holds location and identifying information about users """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
        editable=False,
    )

    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)

    # TODO org should also be discreet choices from this list
    # https://drive.google.com/drive/u/1/folders/1auXpAPhOh4YROnKxOfFy5-T7Ki96aIb6k
    org = models.CharField(blank=True, max_length=100)
    org_type = models.CharField(
        choices=(
            ('NTLS', 'National Society'),
            ('DLGN', 'Delegation'),
            ('SCRT', 'Secretariat'),
            ('ICRC', 'ICRC'),
            ('OTHR', 'Other'),
        ),
        max_length=4,
        blank=True,
    )
    city = models.CharField(blank=True, null=True, max_length=100)
    department = models.CharField(blank=True, null=True, max_length=100)
    position = models.CharField(blank=True, null=True, max_length=100)
    phone_number = models.CharField(blank=True, null=True, max_length=100)

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'

    def __str__(self):
        return self.user.username


class EmergencyOperationsDataset(models.Model):
    is_validated = models.BooleanField(default=False, help_text='Did anyone check the editable data?')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Raw data from the scraper
    raw_file_name = models.TextField(null=True, blank=True)
    raw_file_url = models.TextField(null=True, blank=True)
    raw_appeal_launch_date = models.TextField(null=True, blank=True)
    raw_appeal_number = models.TextField(null=True, blank=True)
    raw_category_allocated = models.TextField(null=True, blank=True)
    raw_date_of_issue = models.TextField(null=True, blank=True)
    raw_dref_allocated = models.TextField(null=True, blank=True)
    raw_expected_end_date = models.TextField(null=True, blank=True)
    raw_expected_time_frame = models.TextField(null=True, blank=True)
    raw_glide_number = models.TextField(null=True, blank=True)
    raw_num_of_people_affected = models.TextField(null=True, blank=True)
    raw_num_of_people_to_be_assisted = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_female = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_male = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_reached = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_targeted = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_requirements = models.TextField(null=True, blank=True)
    raw_health_female = models.TextField(null=True, blank=True)
    raw_health_male = models.TextField(null=True, blank=True)
    raw_health_people_reached = models.TextField(null=True, blank=True)
    raw_health_people_targeted = models.TextField(null=True, blank=True)
    raw_health_requirements = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_female = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_male = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_reached = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_targeted = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_requirements = models.TextField(null=True, blank=True)
    raw_migration_female = models.TextField(null=True, blank=True)
    raw_migration_male = models.TextField(null=True, blank=True)
    raw_migration_people_reached = models.TextField(null=True, blank=True)
    raw_migration_people_targeted = models.TextField(null=True, blank=True)
    raw_migration_requirements = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_female = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_male = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_reached = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_targeted = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_requirements = models.TextField(null=True, blank=True)
    raw_shelter_female = models.TextField(null=True, blank=True)
    raw_shelter_male = models.TextField(null=True, blank=True)
    raw_shelter_people_reached = models.TextField(null=True, blank=True)
    raw_shelter_people_targeted = models.TextField(null=True, blank=True)
    raw_shelter_requirements = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_female = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_male = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_reached = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_targeted = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_requirements = models.TextField(null=True, blank=True)
    raw_education_female = models.TextField(null=True, blank=True)
    raw_education_male = models.TextField(null=True, blank=True)
    raw_education_people_reached = models.TextField(null=True, blank=True)
    raw_education_people_targeted = models.TextField(null=True, blank=True)
    raw_education_requirements = models.TextField(null=True, blank=True)

    # Fields for the cleaned data
    file_name = models.CharField(max_length=200, null=True, blank=True)
    appeal_launch_date = models.DateField(null=True, blank=True)
    appeal_number = models.CharField(max_length=20, null=True, blank=True)
    category_allocated = models.CharField(max_length=100, null=True, blank=True)
    date_of_issue = models.DateField(null=True, blank=True)
    dref_allocated = models.IntegerField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    expected_time_frame = models.IntegerField(null=True, blank=True)
    glide_number = models.CharField(max_length=18, null=True, blank=True)
    num_of_people_affected = models.IntegerField(null=True, blank=True)
    num_of_people_to_be_assisted = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_female = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_male = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_reached = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_targeted = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_requirements = models.IntegerField(null=True, blank=True)
    health_female = models.IntegerField(null=True, blank=True)
    health_male = models.IntegerField(null=True, blank=True)
    health_people_reached = models.IntegerField(null=True, blank=True)
    health_people_targeted = models.IntegerField(null=True, blank=True)
    health_requirements = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_female = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_male = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_reached = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_targeted = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_requirements = models.IntegerField(null=True, blank=True)
    migration_female = models.IntegerField(null=True, blank=True)
    migration_male = models.IntegerField(null=True, blank=True)
    migration_people_reached = models.IntegerField(null=True, blank=True)
    migration_people_targeted = models.IntegerField(null=True, blank=True)
    migration_requirements = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_female = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_male = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_reached = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_targeted = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_requirements = models.IntegerField(null=True, blank=True)
    shelter_female = models.IntegerField(null=True, blank=True)
    shelter_male = models.IntegerField(null=True, blank=True)
    shelter_people_reached = models.IntegerField(null=True, blank=True)
    shelter_people_targeted = models.IntegerField(null=True, blank=True)
    shelter_requirements = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_female = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_male = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_reached = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_targeted = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_requirements = models.IntegerField(null=True, blank=True)
    education_female = models.IntegerField(null=True, blank=True)
    education_male = models.IntegerField(null=True, blank=True)
    education_people_reached = models.IntegerField(null=True, blank=True)
    education_people_targeted = models.IntegerField(null=True, blank=True)
    education_requirements = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Emergency Operations Dataset'
        verbose_name_plural = 'Emergency Operations Datasets'


class EmergencyOperationsPeopleReached(models.Model):
    is_validated = models.BooleanField(default=False, help_text='Did anyone check the editable data?')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Raw data from the scraper
    raw_file_name = models.TextField(null=True, blank=True)
    raw_file_url = models.TextField(null=True, blank=True)
    raw_appeal_number = models.TextField(null=True, blank=True)
    raw_date_of_issue = models.TextField(null=True, blank=True)
    raw_epoa_update_num = models.TextField(null=True, blank=True)
    raw_glide_number = models.TextField(null=True, blank=True)
    raw_operation_start_date = models.TextField(null=True, blank=True)
    raw_operation_timeframe = models.TextField(null=True, blank=True)
    raw_time_frame_covered_by_update = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_female = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_male = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_reached = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_requirements = models.TextField(null=True, blank=True)
    raw_health_female = models.TextField(null=True, blank=True)
    raw_health_male = models.TextField(null=True, blank=True)
    raw_health_people_reached = models.TextField(null=True, blank=True)
    raw_health_requirements = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_female = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_male = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_reached = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_requirements = models.TextField(null=True, blank=True)
    raw_migration_female = models.TextField(null=True, blank=True)
    raw_migration_male = models.TextField(null=True, blank=True)
    raw_migration_people_reached = models.TextField(null=True, blank=True)
    raw_migration_requirements = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_female = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_male = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_reached = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_requirements = models.TextField(null=True, blank=True)
    raw_shelter_female = models.TextField(null=True, blank=True)
    raw_shelter_male = models.TextField(null=True, blank=True)
    raw_shelter_people_reached = models.TextField(null=True, blank=True)
    raw_shelter_requirements = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_female = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_male = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_reached = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_requirements = models.TextField(null=True, blank=True)

    # Fields for the cleaned data
    file_name = models.CharField(max_length=200, null=True, blank=True)
    appeal_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_issue = models.DateField(null=True, blank=True)
    dref_allocated = models.IntegerField(null=True, blank=True)
    epoa_update_num = models.IntegerField(null=True, blank=True)
    glide_number = models.CharField(max_length=18, null=True, blank=True)
    operation_start_date = models.DateField(null=True, blank=True)
    operation_timeframe = models.CharField(max_length=200, null=True, blank=True)
    time_frame_covered_by_update = models.CharField(max_length=200, null=True, blank=True)
    disaster_risk_reduction_female = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_male = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_reached = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_requirements = models.IntegerField(null=True, blank=True)
    health_female = models.IntegerField(null=True, blank=True)
    health_male = models.IntegerField(null=True, blank=True)
    health_people_reached = models.IntegerField(null=True, blank=True)
    health_requirements = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_female = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_male = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_reached = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_requirements = models.IntegerField(null=True, blank=True)
    migration_female = models.IntegerField(null=True, blank=True)
    migration_male = models.IntegerField(null=True, blank=True)
    migration_people_reached = models.IntegerField(null=True, blank=True)
    migration_requirements = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_female = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_male = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_reached = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_requirements = models.IntegerField(null=True, blank=True)
    shelter_female = models.IntegerField(null=True, blank=True)
    shelter_male = models.IntegerField(null=True, blank=True)
    shelter_people_reached = models.IntegerField(null=True, blank=True)
    shelter_requirements = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_female = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_male = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_reached = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_requirements = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Emergency Operations People Reached'
        verbose_name_plural = 'Emergency Operations People Reached'


class EmergencyOperationsEA(models.Model):
    is_validated = models.BooleanField(default=False, help_text='Did anyone check the editable data?')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    raw_file_name = models.TextField(null=True, blank=True)
    raw_file_url = models.TextField(null=True, blank=True)
    raw_appeal_ends = models.TextField(null=True, blank=True)
    raw_appeal_launch_date = models.TextField(null=True, blank=True)
    raw_appeal_number = models.TextField(null=True, blank=True)
    raw_current_operation_budget = models.TextField(null=True, blank=True)
    raw_dref_allocated = models.TextField(null=True, blank=True)
    raw_glide_number = models.TextField(null=True, blank=True)
    raw_num_of_people_to_be_assisted = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_female = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_male = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_reached = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_targeted = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_requirements = models.TextField(null=True, blank=True)
    raw_health_female = models.TextField(null=True, blank=True)
    raw_health_male = models.TextField(null=True, blank=True)
    raw_health_people_reached = models.TextField(null=True, blank=True)
    raw_health_people_targeted = models.TextField(null=True, blank=True)
    raw_health_requirements = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_female = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_male = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_reached = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_targeted = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_requirements = models.TextField(null=True, blank=True)
    raw_migration_female = models.TextField(null=True, blank=True)
    raw_migration_male = models.TextField(null=True, blank=True)
    raw_migration_people_reached = models.TextField(null=True, blank=True)
    raw_migration_people_targeted = models.TextField(null=True, blank=True)
    raw_migration_requirements = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_female = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_male = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_reached = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_targeted = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_requirements = models.TextField(null=True, blank=True)
    raw_shelter_female = models.TextField(null=True, blank=True)
    raw_shelter_male = models.TextField(null=True, blank=True)
    raw_shelter_people_reached = models.TextField(null=True, blank=True)
    raw_shelter_people_targeted = models.TextField(null=True, blank=True)
    raw_shelter_requirements = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_female = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_male = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_reached = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_targeted = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_requirements = models.TextField(null=True, blank=True)

    # Fields for the cleaned data
    file_name = models.CharField(max_length=200, null=True, blank=True)
    appeal_ends = models.DateField(null=True, blank=True)
    appeal_launch_date = models.DateField(null=True, blank=True)
    appeal_number = models.CharField(max_length=20, null=True, blank=True)
    current_operation_budget = models.IntegerField(null=True, blank=True)
    dref_allocated = models.IntegerField(null=True, blank=True)
    glide_number = models.CharField(max_length=18, null=True, blank=True)
    num_of_people_to_be_assisted = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_female = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_male = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_reached = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_targeted = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_requirements = models.IntegerField(null=True, blank=True)
    health_female = models.IntegerField(null=True, blank=True)
    health_male = models.IntegerField(null=True, blank=True)
    health_people_reached = models.IntegerField(null=True, blank=True)
    health_people_targeted = models.IntegerField(null=True, blank=True)
    health_requirements = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_female = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_male = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_reached = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_targeted = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_requirements = models.IntegerField(null=True, blank=True)
    migration_female = models.IntegerField(null=True, blank=True)
    migration_male = models.IntegerField(null=True, blank=True)
    migration_people_reached = models.IntegerField(null=True, blank=True)
    migration_people_targeted = models.IntegerField(null=True, blank=True)
    migration_requirements = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_female = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_male = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_reached = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_targeted = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_requirements = models.IntegerField(null=True, blank=True)
    shelter_female = models.IntegerField(null=True, blank=True)
    shelter_male = models.IntegerField(null=True, blank=True)
    shelter_people_reached = models.IntegerField(null=True, blank=True)
    shelter_people_targeted = models.IntegerField(null=True, blank=True)
    shelter_requirements = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_female = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_male = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_reached = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_targeted = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_requirements = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Emergency Operations Emergency Appeal'
        verbose_name_plural = 'Emergency Operations Emergency Appeals'


class EmergencyOperationsFR(models.Model):
    is_validated = models.BooleanField(default=False, help_text='Did anyone check the editable data?')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    raw_file_name = models.TextField(null=True, blank=True)
    raw_file_url = models.TextField(null=True, blank=True)
    raw_appeal_number = models.TextField(null=True, blank=True)
    raw_date_of_disaster = models.TextField(null=True, blank=True)
    raw_date_of_issue = models.TextField(null=True, blank=True)
    raw_glide_number = models.TextField(null=True, blank=True)
    raw_num_of_other_partner_involved = models.TextField(null=True, blank=True)
    raw_num_of_partner_ns_involved = models.TextField(null=True, blank=True)
    raw_num_of_people_affected = models.TextField(null=True, blank=True)
    raw_num_of_people_to_be_assisted = models.TextField(null=True, blank=True)
    raw_operation_end_date = models.TextField(null=True, blank=True)
    raw_operation_start_date = models.TextField(null=True, blank=True)
    raw_overall_operation_budget = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_female = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_male = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_people_reached = models.TextField(null=True, blank=True)
    #raw_disaster_risk_reduction_people_targeted = models.TextField(null=True, blank=True)
    raw_disaster_risk_reduction_requirements = models.TextField(null=True, blank=True)
    raw_health_female = models.TextField(null=True, blank=True)
    raw_health_male = models.TextField(null=True, blank=True)
    raw_health_people_reached = models.TextField(null=True, blank=True)
    #raw_health_people_targeted = models.TextField(null=True, blank=True)
    raw_health_requirements = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_female = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_male = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_people_reached = models.TextField(null=True, blank=True)
    #raw_livelihoods_and_basic_needs_people_targeted = models.TextField(null=True, blank=True)
    raw_livelihoods_and_basic_needs_requirements = models.TextField(null=True, blank=True)
    raw_migration_female = models.TextField(null=True, blank=True)
    raw_migration_male = models.TextField(null=True, blank=True)
    raw_migration_people_reached = models.TextField(null=True, blank=True)
    #raw_migration_people_targeted = models.TextField(null=True, blank=True)
    raw_migration_requirements = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_female = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_male = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_people_reached = models.TextField(null=True, blank=True)
    #raw_protection_gender_and_inclusion_people_targeted = models.TextField(null=True, blank=True)
    raw_protection_gender_and_inclusion_requirements = models.TextField(null=True, blank=True)
    raw_shelter_female = models.TextField(null=True, blank=True)
    raw_shelter_male = models.TextField(null=True, blank=True)
    raw_shelter_people_reached = models.TextField(null=True, blank=True)
    #raw_shelter_people_targeted = models.TextField(null=True, blank=True)
    raw_shelter_requirements = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_female = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_male = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_people_reached = models.TextField(null=True, blank=True)
    #raw_water_sanitation_and_hygiene_people_targeted = models.TextField(null=True, blank=True)
    raw_water_sanitation_and_hygiene_requirements = models.TextField(null=True, blank=True)

    # Fields for the cleaned data
    file_name = models.CharField(max_length=200, null=True, blank=True)
    appeal_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_disaster = models.DateField(null=True, blank=True)
    date_of_issue = models.DateField(null=True, blank=True)
    glide_number = models.CharField(max_length=18, null=True, blank=True)
    num_of_other_partner_involved = models.TextField(null=True, blank=True)
    num_of_partner_ns_involved = models.TextField(null=True, blank=True)
    num_of_people_affected = models.IntegerField(null=True, blank=True)
    num_of_people_to_be_assisted = models.IntegerField(null=True, blank=True)
    operation_end_date = models.DateField(null=True, blank=True)
    operation_start_date = models.DateField(null=True, blank=True)
    overall_operation_budget = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_female = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_male = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_people_reached = models.IntegerField(null=True, blank=True)
    #disaster_risk_reduction_people_targeted = models.IntegerField(null=True, blank=True)
    disaster_risk_reduction_requirements = models.IntegerField(null=True, blank=True)
    health_female = models.IntegerField(null=True, blank=True)
    health_male = models.IntegerField(null=True, blank=True)
    health_people_reached = models.IntegerField(null=True, blank=True)
    #health_people_targeted = models.IntegerField(null=True, blank=True)
    health_requirements = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_female = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_male = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_people_reached = models.IntegerField(null=True, blank=True)
    #livelihoods_and_basic_needs_people_targeted = models.IntegerField(null=True, blank=True)
    livelihoods_and_basic_needs_requirements = models.IntegerField(null=True, blank=True)
    migration_female = models.IntegerField(null=True, blank=True)
    migration_male = models.IntegerField(null=True, blank=True)
    migration_people_reached = models.IntegerField(null=True, blank=True)
    #migration_people_targeted = models.IntegerField(null=True, blank=True)
    migration_requirements = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_female = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_male = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_people_reached = models.IntegerField(null=True, blank=True)
    #protection_gender_and_inclusion_people_targeted = models.IntegerField(null=True, blank=True)
    protection_gender_and_inclusion_requirements = models.IntegerField(null=True, blank=True)
    shelter_female = models.IntegerField(null=True, blank=True)
    shelter_male = models.IntegerField(null=True, blank=True)
    shelter_people_reached = models.IntegerField(null=True, blank=True)
    #shelter_people_targeted = models.IntegerField(null=True, blank=True)
    shelter_requirements = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_female = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_male = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_people_reached = models.IntegerField(null=True, blank=True)
    #water_sanitation_and_hygiene_people_targeted = models.IntegerField(null=True, blank=True)
    water_sanitation_and_hygiene_requirements = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Emergency Operations Final Report'
        verbose_name_plural = 'Emergency Operations Final Reports'


class CronJobStatus(IntEnum):
    NEVER_RUN = -1
    SUCCESSFUL = 0
    WARNED = 1
    ERRONEOUS = 2

class CronJob(models.Model):
    """ CronJob log row about jobs results """
    name = models.CharField(max_length=100, default = '')
    status = EnumIntegerField(CronJobStatus, default=-1)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)
    num_result = models.IntegerField(default=0)
    storing_days = models.IntegerField(default=3)
    backend_side = models.BooleanField(default=True) # We could keep backend/frontend ingest results here also

    class Meta:
        verbose_name = 'Cronjob log record'
        verbose_name_plural = 'Cronjob log records'

    def __str__(self):
        if self.num_result:
            return '%s | %s : %s | %s' % (self.name, str(self.status), str(self.num_result), str(self.created_at)[5:16])
        else:
            return '%s | %s | %s'      % (self.name, str(self.status),                       str(self.created_at)[5:16]) # omit irrelevant 0

    # Given a request containing new CronJob log row, validate and add the CronJob log row.
    def sync_cron(body):
        new = []
        errors = []
        fields = { 'name': body['name'], 'message': body['message'] }
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
            store_me = 3 # default storing days

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
            CronJob.objects.filter(name=body['name'], created_at__lt=datetime.now(pytz.timezone('UTC'))-timedelta(days=store_me)).delete() # Delete old ones, "log-rotate"
            CronJob.objects.bulk_create(new)

        return errors, new

# To find related scripts from go-api root dir: grep -rl CronJob --exclude-dir=__pycache__ --exclude-dir=main --exclude-dir=migrations --exclude=CHANGELOG.md *

from .triggers import *
