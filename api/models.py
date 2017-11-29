from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from enumfields import EnumIntegerField
from enumfields import Enum


class DisasterType(models.Model):
    """ summary of disaster """
    name = models.CharField(max_length=100)
    summary = models.TextField()

    def __str__(self):
        return self.name


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    eid = models.IntegerField(null=True)
    name = models.CharField(max_length=100)
    dtype = models.ForeignKey(DisasterType, null=True)
    summary = models.TextField(blank=True)
    status = models.CharField(max_length=30, blank=True)
    region = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=20, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def countries(self):
        """ Get countries from all appeals and field reports in this disaster """
        countries = [country for fr in self.fieldreport_set.all() for country in fr.countries.all()] + \
                    [appeal.country for appeal in self.appeal_set.all()]
        return list(set([c.name for c in countries]))

    def start_date(self):
        """ Get start date of first appeal """
        return min([a['start_date'] for a in self.appeal_set.all()])

    def end_date(self):
        """ Get latest end date of all appeals """
        return max([a['end_date'] for a in self.appeal_set.all()])

    def __str__(self):
        return self.name


class Country(models.Model):
    """ A country """

    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=2, null=True)
    society_name = models.TextField(default="")

    def __str__(self):
        return self.name


class Action(models.Model):
    """ Action taken """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ActionsTaken(models.Model):
    """ All the actions taken by an organization """

    organization = models.CharField(max_length=100)
    actions = models.ManyToManyField(Action)
    summary = models.TextField(blank=True)

    def __str__(self):
        return self.organization


class Document(models.Model):
    """ A document, located somwehere """

    name = models.CharField(max_length=100)
    uri = models.TextField()

    def __str__(self):
        return self.name


class AppealType(Enum):
    """ summarys of appeals """
    DREF = 0
    APPEAL = 1


class Appeal(models.Model):
    """ An appeal for a disaster and country, containing documents """

    # appeal ID, assinged by creator
    aid = models.CharField(max_length=20)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    atype = EnumIntegerField(AppealType, default=0)

    event = models.ForeignKey(Event, null=True)
    country = models.ForeignKey(Country, null=True)
    sector = models.CharField(max_length=100, blank=True)

    num_beneficiaries = models.IntegerField(default=0)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_funded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    # documents = models.ManyToManyField(Document)

    def __str__(self):
        return self.aid


class Contact(models.Model):
    """ Contact """

    organization = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    email = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class FieldReport(models.Model):
    """ A field report for a disaster and country, containing documents """

    rid = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    description = models.TextField(blank=True, default='')
    dtype = models.ForeignKey(DisasterType)
    event = models.ForeignKey(Event, null=True)
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

    # action IDs - other tables?
    actions_taken = models.ManyToManyField(ActionsTaken)

    # contacts
    contacts = models.ManyToManyField(Contact)
    created_at = models.DateTimeField(auto_now_add=True)

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
