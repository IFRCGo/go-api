from django.db import models
from django.conf import settings
from django.utils import timezone
from enumfields import IntEnum, EnumIntegerField
from .storage import AzureStorage
from tinymce import HTMLField
from django.core.validators import FileExtensionValidator

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
    society_name = models.TextField(blank=True)
    society_url = models.URLField(blank=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    overview = models.TextField(blank=True, null=True)
    key_priorities = models.TextField(blank=True, null=True)
    inform_score = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=3)
    #logo = models.FileField(blank=True, null=True, upload_to='documents/', # for local tests
    logo = models.FileField(blank=True, null=True, upload_to=logo_document_path,
        storage=AzureStorage(), validators=[FileExtensionValidator(allowed_extensions=['png','jpg','gif'])])


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
    dtype = models.ForeignKey(DisasterType, null=True, on_delete=models.SET_NULL)
    districts = models.ManyToManyField(District, blank=True)
    countries = models.ManyToManyField(Country)
    regions = models.ManyToManyField(Region)
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
    is_featured = models.BooleanField(default=False)
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

    num_injured = models.IntegerField(null=True, blank=True)
    num_dead = models.IntegerField(null=True, blank=True)
    num_missing = models.IntegerField(null=True, blank=True)
    num_affected = models.IntegerField(null=True, blank=True)
    num_displaced = models.IntegerField(null=True, blank=True)
    num_assisted = models.IntegerField(null=True, blank=True)
    num_localstaff = models.IntegerField(null=True, blank=True)
    num_volunteers = models.IntegerField(null=True, blank=True)
    num_expats_delegates = models.IntegerField(null=True, blank=True)

    gov_num_injured = models.IntegerField(null=True, blank=True)
    gov_num_dead = models.IntegerField(null=True, blank=True)
    gov_num_missing = models.IntegerField(null=True, blank=True)
    gov_num_affected = models.IntegerField(null=True, blank=True)
    gov_num_displaced = models.IntegerField(null=True, blank=True)
    gov_num_assisted = models.IntegerField(null=True, blank=True)

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
        # On save, is report_date is not set, set it to now.
        if not self.id and not self.report_date:
            self.report_date = timezone.now()
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
    field_report = models.ForeignKey(FieldReport, related_name='contacts', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.name, self.title)


class Action(models.Model):
    """ Action taken """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ActionsTaken(models.Model):
    """ All the actions taken by an organization """

    organization = models.CharField(
        choices=(
            ('NTLS', 'National Society'),
            ('PNS', 'Foreign Society'),
            ('FDRN', 'Federation'),
        ),
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


from .triggers import *
