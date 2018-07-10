from django.db import models
from enumfields import EnumIntegerField
from enumfields import IntEnum
from api.models import District, Country, Region, Event, DisasterType
from datetime import datetime


DATE_FORMAT = '%Y/%m/%d %H:%M'


class ERUType(IntEnum):
    BASECAMP = 0
    TELECOM = 1
    LOGISTICS = 2
    EMERGENCY_HOSPITAL = 3
    EMERGENCY_CLINIC = 4
    RELIEF = 5
    WASH_15 = 6
    WASH_20 = 7
    WASH_40 = 8


class ERUOwner(models.Model):
    """ A resource that may or may not be deployed """

    national_society_country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ERUs from a National Society'
        verbose_name_plural = 'ERUs'

    def __str__(self):
        if self.national_society_country.society_name is not None:
            return '%s (%s)' % (self.national_society_country.society_name, self.national_society_country.name)
        return self.national_society_country.name


class ERU(models.Model):
    """ A resource that can be deployed """
    type = EnumIntegerField(ERUType, default=0)
    units = models.IntegerField(default=0)
    equipment_units = models.IntegerField(default=0)
    # where deployed (none if available)
    deployed_to = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    # links to services
    eru_owner = models.ForeignKey(ERUOwner, on_delete=models.CASCADE)
    available = models.BooleanField(default=False)


    def __str__(self):
        return ['Basecamp', 'IT & Telecom', 'Logistics', 'RCRC Emergency Hospital', 'RCRC Emergency Clinic', 'Relief', 'WASH M15', 'WASH MSM20', 'WASH M40'][self.type]


class Heop(models.Model):
    """ A deployment of a head officer"""
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)

    person = models.CharField(null=True, blank=True, max_length=100)
    role = models.CharField(default='HeOps', null=True, blank=True, max_length=32)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'HeOp'
        verbose_name_plural = 'HeOps'

    def __str__(self):
        return '%s (%s) %s - %s' % (self.person, self.country,
                                    datetime.strftime(self.start_date, DATE_FORMAT),
                                    datetime.strftime(self.end_date, DATE_FORMAT))


class Fact(models.Model):
    """ A FACT resource"""
    start_date = models.DateTimeField(null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s %s' % (self.country, datetime.strftime(self.start_date, DATE_FORMAT))

    class Meta:
        verbose_name = 'FACT'
        verbose_name_plural = 'FACTs'


class Rdrt(models.Model):
    """ An RDRT/RIT resource"""
    start_date = models.DateTimeField(null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s %s' % (self.country, datetime.strftime(self.start_date, DATE_FORMAT))

    class Meta:
        verbose_name = 'RDRT/RIT'
        verbose_name_plural = 'RDRTs/RITs'


class DeployedPerson(models.Model):
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    name = models.CharField(null=True, blank=True, max_length=100)
    role = models.CharField(null=True, blank=True, max_length=32)
    def __str__(self):
        return '%s - %s' % (self.name, self.role)


class FactPerson(DeployedPerson):
    society_deployed_from = models.CharField(null=True, blank=True, max_length=100)
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'FACT Person'
        verbose_name_plural = 'FACT People'


class RdrtPerson(DeployedPerson):
    society_deployed_from = models.CharField(null=True, blank=True, max_length=100)
    rdrt = models.ForeignKey(Rdrt, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'RDRT/RIT Person'
        verbose_name_plural = 'RDRT/RIT People'


class PartnerSocietyActivities(models.Model):
    activity = models.CharField(max_length=50)
    def __str__(self):
        return self.activity


class PartnerSocietyDeployment(DeployedPerson):
    activity = models.ForeignKey(PartnerSocietyActivities, related_name='partner_societies', null=True, on_delete=models.CASCADE)
    parent_society = models.ForeignKey(Country, related_name='partner_society_members', null=True, on_delete=models.SET_NULL)
    country_deployed_to = models.ForeignKey(Country, related_name='country_partner_deployments', null=True, on_delete=models.SET_NULL)
    district_deployed_to = models.ManyToManyField(District)
    def __str__(self):
        return '%s deployment in %s' % (self.parent_society, self.country_deployed_to)
