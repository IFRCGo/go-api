from datetime import datetime
from enumfields import EnumIntegerField
from enumfields import IntEnum

from django.db import models
from django.conf import settings
from django.utils.hashable import make_hashable
from django.utils.encoding import force_str
from django.contrib.postgres.fields import ArrayField

from api.models import District, Country, Region, Event, DisasterType, Appeal

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
    num_people_deployed = models.IntegerField(default=0, help_text='Still not used in frontend')
    # where deployed (none if available)
    deployed_to = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    appeal = models.ForeignKey(Appeal, null=True, blank=True, on_delete=models.SET_NULL, help_text='Still not used in frontend')
    # links to services
    eru_owner = models.ForeignKey(ERUOwner, on_delete=models.CASCADE)
    supporting_societies = models.CharField(null=True, blank=True, max_length=500, help_text='Still not used in frontend')
    start_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    end_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    available = models.BooleanField(default=False)
    alert_date = models.DateTimeField(null=True, help_text='Still not used in frontend')

    def __str__(self):
        return ['Basecamp', 'IT & Telecom', 'Logistics', 'RCRC Emergency Hospital', 'RCRC Emergency Clinic', 'Relief', 'WASH M15', 'WASH MSM20', 'WASH M40'][self.type]


class PersonnelDeployment(models.Model):
    country_deployed_to = models.ForeignKey(Country, on_delete=models.CASCADE)
    region_deployed_to = models.ForeignKey(Region, on_delete=models.CASCADE)
    event_deployed_to = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    appeal_deployed_to = models.ForeignKey(Appeal, null=True, blank=True, on_delete=models.SET_NULL, help_text='Still not used in frontend')
    alert_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    exp_start_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    end_duration = models.CharField(null=True, blank=True, max_length=100, help_text='Still not used in frontend')
    start_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    end_date = models.DateTimeField(null=True, help_text='Still not used in frontend')
    created_at = models.DateTimeField(auto_now_add=True) #, default = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta('1 year'))
    updated_at = models.DateTimeField(auto_now=True)
    previous_update = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Personnel Deployments'

    def __str__(self):
        return '%s, %s' % (self.country_deployed_to, self.region_deployed_to)


class DeployedPerson(models.Model):
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    name = models.CharField(null=True, blank=True, max_length=100)
    role = models.CharField(null=True, blank=True, max_length=32)

    def __str__(self):
        return '%s - %s' % (self.name, self.role)


class Personnel(DeployedPerson):
    type = models.CharField(
        choices=(
            ('fact', 'FACT'),
            ('heop', 'HEOP'),
            ('rdrt', 'RDRT'),
            ('ifrc', 'IFRC'),
            ('eru', 'ERU HR'),
            ('rr', 'Rapid Response'),
        ),
        max_length=4,
    )
    country_from = models.ForeignKey(Country, related_name='personnel_deployments', null=True, on_delete=models.SET_NULL)
    deployment = models.ForeignKey(PersonnelDeployment, on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s - %s' % (self.type.upper(), self.name, self.role)

    class Meta:
        verbose_name_plural = 'Personnel'


class PartnerSocietyActivities(models.Model):
    activity = models.CharField(max_length=50)

    def __str__(self):
        return self.activity

    class Meta:
        verbose_name = 'Partner society activity'
        verbose_name_plural = 'Partner society activities'


class PartnerSocietyDeployment(DeployedPerson):
    activity = models.ForeignKey(PartnerSocietyActivities, related_name='partner_societies', null=True, on_delete=models.CASCADE)
    parent_society = models.ForeignKey(Country, related_name='partner_society_members', null=True, on_delete=models.SET_NULL)
    country_deployed_to = models.ForeignKey(Country, related_name='country_partner_deployments', null=True, on_delete=models.SET_NULL)
    district_deployed_to = models.ManyToManyField(District)

    def __str__(self):
        return '%s deployment in %s' % (self.parent_society, self.country_deployed_to)


class ProgrammeTypes(IntEnum):
    BILATERAL = 0
    MULTILATERAL = 1
    DOMESTIC = 2


class Sectors(IntEnum):
    WASH = 0
    PGI = 1
    CEA = 2
    MIGRATION = 3
    HEALTH = 4
    DRR = 5
    SHELTER = 6
    NS_STRENGTHENING = 7
    EDUCATION = 8
    LIVELIHOODS_AND_BASIC_NEEDS = 9

    class Labels:
        WASH = 'WASH'
        PGI = 'PGI'
        CEA = 'CEA'
        MIGRATION = 'Migration'
        HEALTH = 'Health'
        DRR = 'DRR'
        SHELTER = 'Shelter'
        NS_STRENGTHENING = 'NS Strengthening'
        EDUCATION = 'Education'
        LIVELIHOODS_AND_BASIC_NEEDS = 'Livelihoods and basic needs'


class SectorTags(IntEnum):
    WASH = 0
    PGI = 1
    CEA = 2
    MIGRATION = 3
    DRR = 5
    SHELTER = 6
    NS_STRENGTHENING = 7
    EDUCATION = 8
    LIVELIHOODS_AND_BASIC_NEEDS = 9
    RECOVERY = 10
    INTERNAL_DISPLACEMENT = 11
    HEALTH_PUBLIC = 4
    HEALTH_CLINICAL = 12
    COVID_19 = 13
    RCCE = 14

    class Labels:
        WASH = 'WASH'
        PGI = 'PGI'
        CEA = 'CEA'
        MIGRATION = 'Migration'
        DRR = 'DRR'
        SHELTER = 'Shelter'
        NS_STRENGTHENING = 'NS Strengthening'
        EDUCATION = 'Education'
        LIVELIHOODS_AND_BASIC_NEEDS = 'Livelihoods and basic needs'
        RECOVERY = 'Recovery'
        INTERNAL_DISPLACEMENT = 'Internal displacement'
        HEALTH_PUBLIC = 'Health (public)'
        HEALTH_CLINICAL = 'Health (clinical)'
        COVID_19 = 'COVID-19'
        RCCE = 'RCCE'


class Statuses(IntEnum):
    PLANNED = 0
    ONGOING = 1
    COMPLETED = 2


class OperationTypes(IntEnum):
    PROGRAMME = 0
    EMERGENCY_OPERATION = 1


class RegionalProject(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    PUBLIC = 'public'
    LOGGED_IN_USER = 'logged_in_user'
    IFRC_ONLY = 'ifrc_only'

    VISIBILITY = (
        (PUBLIC, 'Public'),
        (LOGGED_IN_USER, 'Logged in user'),
        (IFRC_ONLY, 'IFRC only'),
    )

    modified_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
    )  # user who created this project
    reporting_ns = models.ForeignKey(
        Country, on_delete=models.CASCADE,
        related_name='ns_projects',
    )  # this is the national society that is reporting the project
    project_country = models.ForeignKey(
        Country, on_delete=models.CASCADE,
        null=True,  # NOTE: Added due to migrations issue
        related_name='projects',
    )  # this is the country where the project is actually taking place
    project_districts = models.ManyToManyField(
        District, blank=True,
        help_text='No selection will indicate all districts.',
    )  # this is the district where the project is actually taking place
    event = models.ForeignKey(
        Event, null=True, blank=True, on_delete=models.SET_NULL,
    )  # this is the current operation
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.TextField()
    programme_type = EnumIntegerField(ProgrammeTypes)
    primary_sector = EnumIntegerField(Sectors)
    secondary_sectors = ArrayField(
        EnumIntegerField(SectorTags),
        default=list, blank=True,
    )
    operation_type = EnumIntegerField(OperationTypes)
    start_date = models.DateField()
    end_date = models.DateField()
    budget_amount = models.IntegerField()
    status = EnumIntegerField(Statuses)

    # Target Metric
    target_male = models.IntegerField(null=True, blank=True)
    target_female = models.IntegerField(null=True, blank=True)
    target_other = models.IntegerField(null=True, blank=True)
    target_total = models.IntegerField(null=True, blank=True)

    # Reached Metric
    reached_male = models.IntegerField(null=True, blank=True)
    reached_female = models.IntegerField(null=True, blank=True)
    reached_other = models.IntegerField(null=True, blank=True)
    reached_total = models.IntegerField(null=True, blank=True)

    regional_project = models.ForeignKey(
        RegionalProject, null=True, blank=True, on_delete=models.SET_NULL
    )
    visibility = models.CharField(max_length=32, choices=VISIBILITY, default=PUBLIC)

    def __str__(self):
        if self.reporting_ns is None:
            postfix = None
        else:
            postfix = self.reporting_ns.society_name
        return '%s (%s)' % (self.name, postfix)

    def get_secondary_sectors_display(self):
        choices_dict = dict(make_hashable(SectorTags.choices()))
        return [
            force_str(choices_dict.get(make_hashable(value), value), strings_only=True)
            for value in self.secondary_sectors or []
        ]

    @classmethod
    def get_for(cls, user, queryset=None):
        qs = cls.objects.all() if queryset is None else queryset
        if user.is_authenticated:
            if user.email and user.email.endswith('@ifrc.org'):
                return qs
            return qs.exclude(visibility=Project.IFRC_ONLY)
        return qs.filter(visibility=Project.PUBLIC)


class ProjectImport(models.Model):
    """
    Track Project Imports (For Django Admin Panel)
    """
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILURE = 'failure'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failure'),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )  # user who created this project import
    created_at = models.DateTimeField(auto_now_add=True)
    projects_created = models.ManyToManyField(Project)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    file = models.FileField(upload_to='project-imports/')

    def __str__(self):
        return f'Project Import {self.status}:{self.created_at}'


class ERUReadiness(models.Model):
    """ ERU Readiness concerning personnel and equipment """
    national_society = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    ERU_type = EnumIntegerField(ERUType, default=0)
    is_personnel = models.BooleanField(default=False)
    is_equipment = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at', 'national_society', )
        verbose_name = 'ERU Readiness'
        verbose_name_plural = 'NS-es ERU Readiness'

    def __str__(self):
        if self.national_society is None:
            name = None
        else:
            name = self.national_society
        return '%s (%s)' % (self.ERU_type, name)


###############################################################################
####################### Deprecated tables #####################################
# https://github.com/IFRCGo/go-frontend/issues/335
###############################################################################


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
