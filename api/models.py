from django.db import models
from django.conf import settings
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from .storage import AzureStorage


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

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'MENA'][self.name]


class Country(models.Model):
    """ A country """

    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=2, null=True)
    society_name = models.TextField(blank=True)
    society_url = models.URLField(blank=True)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    name = models.CharField(max_length=100)
    dtype = models.ForeignKey(DisasterType, null=True, on_delete=models.SET_NULL)
    countries = models.ManyToManyField(Country)
    regions = models.ManyToManyField(Region)
    summary = models.TextField(blank=True)
    num_affected = models.IntegerField(null=True, blank=True)
    glide = models.CharField(max_length=18, blank=True)

    disaster_start_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    auto_generated = models.BooleanField(default=False)

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
            'name': self.name,
            'dtype': getattr(self.dtype, 'name', None),
            'location': ', '.join(map(str, countries)) if len(countries) else None,
            'summary': self.summary,
            'date': self.disaster_start_date,
        }

    def es_id(self):
        return 'event-%s' % self.id

    def es_index(self):
        return 'page_event'

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
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.name, self.title)


class KeyFigure(models.Model):
    event = models.ForeignKey(Event)
    # key figure metric
    number = models.IntegerField()
    # key figure units
    deck = models.CharField(max_length=50)
    # key figure website link, publication
    source = models.CharField(max_length=256)


class Snippet(models.Model):
    """ Snippet of text """
    snippet = models.CharField(max_length=300)
    event = models.ForeignKey(Event)


def sitrep_document_path(instance, filename):
    return 'sitreps/%s/%s' % (instance.event.id, filename)


class SituationReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    document = models.FileField(null=True, blank=True, upload_to=sitrep_document_path, storage=AzureStorage())
    document_url = models.URLField(blank=True)

    event = models.ForeignKey(Event, on_delete=models.CASCADE)

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
    alert_level = models.CharField(max_length=16)
    alert_score = models.CharField(max_length=16, null=True)
    severity = models.TextField()
    severity_unit = models.CharField(max_length=16)
    severity_value = models.CharField(max_length=16)
    population_unit = models.CharField(max_length=16)
    population_value = models.CharField(max_length=16)
    vulnerability = models.IntegerField()
    countries = models.ManyToManyField(Country)
    country_text = models.TextField()


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
    code = models.CharField(max_length=20, null=True)
    sector = models.CharField(max_length=100, blank=True)

    num_beneficiaries = models.IntegerField(default=0)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_funded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    event = models.ForeignKey(Event, related_name='appeals', null=True, blank=True, on_delete=models.SET_NULL)
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
        ordering = ('-end_date', '-start_date',)

    def indexing(self):
        return {
            'id': self.id,
            'name': self.name,
            'dtype': getattr(self.dtype, 'name', None),
            'location': getattr(self.country, 'name', None),
            'date': self.start_date,
        }

    def es_id(self):
        return 'appeal-%s' % self.id

    def es_index(self):
        return 'page_appeal'

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
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    document = models.FileField(null=True, blank=True, upload_to=appeal_document_path, storage=AzureStorage())
    document_url = models.URLField(blank=True)

    appeal = models.ForeignKey(Appeal, on_delete=models.CASCADE)

    def __str__(self):
        return '%s - %s' % (self.appeal, self.name)


class RequestChoices(IntEnum):
    NO = 0
    REQUESTED = 1
    PLANNED = 2
    COMPLETE = 3


class VisibilityChoices(IntEnum):
    MEMBERSHIP = 1
    IFRC = 2
    PUBLIC = 3


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
    description = models.TextField(blank=True, default='')
    dtype = models.ForeignKey(DisasterType, on_delete=models.PROTECT)
    event = models.ForeignKey(Event, related_name='field_reports', null=True, blank=True, on_delete=models.SET_NULL)
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

    # meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-updated_at',)

    def indexing(self):
        countries = [c.name for c in self.countries.all()]
        return {
            'id': self.id,
            'name': self.summary,
            'dtype': getattr(self.dtype, 'name', None),
            'location': ', '.join(map(str, countries)) if len(countries) else None,
            'summary': self.description,
            'date': self.created_at,
        }

    def es_id(self):
        return 'fieldreport-%s' % self.id

    def es_index(self):
        return 'page_report'

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
    field_report = models.ForeignKey(FieldReport, on_delete=models.CASCADE)

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
    field_report = models.ForeignKey(FieldReport, on_delete=models.CASCADE)

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
    field_report = models.ForeignKey(FieldReport, on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.stype.name, self.spec)


class Profile(models.Model):
    """ Holds location and identifying information about users """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
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
