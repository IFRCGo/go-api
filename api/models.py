import os
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from .esconnection import ES_CLIENT


class DisasterType(models.Model):
    """ summary of disaster """
    name = models.CharField(max_length=100)
    summary = models.TextField()

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

    def __str__(self):
        return ['AFRICA', 'AMERICAS', 'ASIA_PACIFIC', 'EUROPE', 'MENA'][self.name]


class Country(models.Model):
    """ A country """

    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=2, null=True)
    society_name = models.TextField(blank=True)
    society_url = models.URLField(blank=True)
    region = models.ForeignKey(Region, null=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    name = models.CharField(max_length=100)
    dtype = models.ForeignKey(DisasterType, null=True)
    countries = models.ManyToManyField(Country)
    regions = models.ManyToManyField(Region)
    summary = models.TextField(blank=True)

    disaster_start_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    auto_generated = models.BooleanField(default=False)

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
        }

    def es_id(self):
        return 'event-%s' % self.id

    def es_index(self):
        return 'page_event'

    def save(self, *args, **kwargs):
        # On save, if `disaster_start_date` is not set, make it the current time
        if not self.id and not self.disaster_start_date:
            self.disaster_start_date = timezone.now()
        return super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return '%s: %s' % (self.organization, self.summary)


class AppealType(IntEnum):
    """ summarys of appeals """
    DREF = 0
    APPEAL = 1
    INTL = 2


class Appeal(models.Model):
    """ An appeal for a disaster and country, containing documents """

    # appeal ID, assinged by creator
    aid = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    dtype = models.ForeignKey(DisasterType)
    atype = EnumIntegerField(AppealType, default=0)

    status = models.CharField(max_length=30, blank=True)
    code = models.CharField(max_length=20, null=True)
    sector = models.CharField(max_length=100, blank=True)

    num_beneficiaries = models.IntegerField(default=0)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_funded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    event = models.ForeignKey(Event, related_name='appeals', null=True)
    country = models.ForeignKey(Country, null=True)
    region = models.ForeignKey(Region, null=True)

    def indexing(self):
        return {
            'id': self.aid,
            'name': self.name,
            'dtype': getattr(self.dtype, 'name', None),
            'location': getattr(self.country, 'name', None),
        }

    def es_id(self):
        return 'appeal-%s' % self.id

    def es_index(self):
        return 'page_appeal'

    def __str__(self):
        return self.aid


class Contact(models.Model):
    """ Contact """

    ctype = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    email = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class SourceType(models.Model):
    """ Types of sources """
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class Source(models.Model):
    """ Source of information """
    stype = models.ForeignKey(SourceType)
    spec = models.TextField(blank=True)

    def __str__(self):
        return '%s: %s' % (self.stype.name, self.spec)


class RequestChoices(IntEnum):
    NO = 0
    REQUESTED = 1
    PLANNED = 2
    COMPLETE = 3


class FieldReport(models.Model):
    """ A field report for a disaster and country, containing documents """

    originator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    rid = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    description = models.TextField(blank=True, default='')
    dtype = models.ForeignKey(DisasterType)
    event = models.ForeignKey(Event, related_name='field_reports', null=True)
    countries = models.ManyToManyField(Country)
    status = models.IntegerField(default=0)
    request_assistance = models.BooleanField(default=False)

    num_injured = models.IntegerField(null=True)
    num_dead = models.IntegerField(null=True)
    num_missing = models.IntegerField(null=True)
    num_affected = models.IntegerField(null=True)
    num_displaced = models.IntegerField(null=True)
    num_assisted = models.IntegerField(null=True)
    num_localstaff = models.IntegerField(null=True)
    num_volunteers = models.IntegerField(null=True)
    num_expats_delegates = models.IntegerField(null=True)

    gov_num_injured = models.IntegerField(null=True)
    gov_num_dead = models.IntegerField(null=True)
    gov_num_missing = models.IntegerField(null=True)
    gov_num_affected = models.IntegerField(null=True)
    gov_num_displaced = models.IntegerField(null=True)
    gov_num_assisted = models.IntegerField(null=True)

    # actions taken
    actions_taken = models.ManyToManyField(ActionsTaken)
    actions_others = models.TextField(blank=True)

    # information
    sources = models.ManyToManyField(Source)
    bulletin = EnumIntegerField(RequestChoices, default=0)
    dref = EnumIntegerField(RequestChoices, default=0)
    dref_amount = models.IntegerField(null=True)
    appeal = EnumIntegerField(RequestChoices, default=0)
    appeal_amount = models.IntegerField(null=True)

    # disaster response
    rdrt = EnumIntegerField(RequestChoices, default=0)
    num_rdrt = models.IntegerField(null=True)
    fact = EnumIntegerField(RequestChoices, default=0)
    num_fact = models.IntegerField(null=True)
    ifrc_staff = EnumIntegerField(RequestChoices, default=0)
    num_ifrc_staff = models.IntegerField(null=True)
    #eru = EnumIntegerField(RequestChoices, default=0)

    # contacts
    contacts = models.ManyToManyField(Contact)

    # meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def indexing(self):
        countries = [getattr(c, 'name') for c in self.countries.all()]
        return {
            'id': self.rid,
            'name': self.summary,
            'dtype': getattr(self.dtype, 'name', None),
            'location': ','.join(map(str, countries)) if len(countries) else None,
            'summary': self.description,
        }

    def es_id(self):
        return 'fieldreport-%s' % self.id

    def es_index(self):
        return 'page_report'

    def __str__(self):
        return self.rid


class Service(models.Model):
    """ A resource that may or may not be deployed """

    name = models.CharField(max_length=100)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    deployed = models.BooleanField(default=False)
    location = models.TextField()

    def __str__(self):
        return self.name


class Profile(models.Model):
    """ Holds location and identifying information about users """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
    )

    country = models.ForeignKey(Country, null=True)

    # TODO org should also be discreet choices from this list
    # https://drive.google.com/drive/u/1/folders/1auXpAPhOh4YROnKxOfFy5-T7Ki96aIb6k
    org = models.CharField(blank=True, max_length=100)
    org_type = models.CharField(
        choices=(
            ('NTLS', 'National Society'),
            ('DLGN', 'Delegation'),
            ('SCRT', 'Secretariat'),
            ('ICRC', 'ICRC'),
        ),
        max_length=4,
        blank=True,
    )
    city = models.CharField(blank=True, max_length=100)
    department = models.CharField(blank=True, max_length=100)
    position = models.CharField(blank=True, max_length=100)
    phone_number = models.CharField(blank=True, max_length=100)

    def __str__(self):
        return self.user.username


# Save a user profile whenever we create a user
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
post_save.connect(create_profile, sender=settings.AUTH_USER_MODEL)


def index_es(sender, instance, created, **kwargs):
    if ES_CLIENT is not None:
        ES_CLIENT.index(
            index=instance.es_index(),
            doc_type='page',
            id=instance.es_id(),
            body=instance.indexing(),
        )


# Avoid automatic indexing during bulk imports
if os.environ.get('BULK_IMPORT') != '1' and ES_CLIENT is not None:
    post_save.connect(index_es, sender=Event)
    post_save.connect(index_es, sender=Appeal)
    post_save.connect(index_es, sender=FieldReport)
