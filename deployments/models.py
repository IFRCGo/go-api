import reversion
from datetime import datetime
from tinymce import HTMLField

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.db.models import JSONField

from api.models import (
    District,
    Country,
    Region,
    Admin2,
    Event,
    DisasterType,
    Appeal,
    Profile,
    UserCountry,
    VisibilityCharChoices,
    GeneralDocument,
)

DATE_FORMAT = "%Y/%m/%d %H:%M"


class ERUType(models.IntegerChoices):
    BASECAMP = 0, _("Basecamp")
    TELECOM = 1, _("IT & Telecom")
    LOGISTICS = 2, _("Logistics")
    EMERGENCY_HOSPITAL = 3, _("RCRC Emergency Hospital")
    EMERGENCY_CLINIC = 4, _("RCRC Emergency Clinic")
    RELIEF = 5, _("Relief")
    WASH_15 = 6, _("Wash M15")
    WASH_20 = 7, _("Wash MSM20")
    WASH_40 = 8, _("Wash M40")
    WATER_SUPPLY = 9, _("Water Supply and rehabilitation")
    WATER_TREATMENT = 10, _("Household Water Treatment and safe storage")
    COLERA_MANAGEMENT = 11, _("Cholera Case management at Community level")
    BURIALS = 12, _("Safe and Dignified Burials")
    CBS = 13, _("Community Based Surveillance")
    BASECAMP_S = 14, _("Base Camp – S")
    BASECAMP_M = 15, _("Base Camp – M")
    BASECAMP_L = 16, _("Base Camp – L")


@reversion.register()
class ERUOwner(models.Model):
    """A resource that may or may not be deployed"""

    national_society_country = models.ForeignKey(
        Country, verbose_name=_("national society country"), null=True, on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("ERUs from a National Society")
        verbose_name_plural = _("ERUs")

    def __str__(self):
        if self.national_society_country.society_name is not None:
            return "%s (%s)" % (self.national_society_country.society_name, self.national_society_country.name)
        return self.national_society_country.name


@reversion.register()
class ERU(models.Model):
    """A resource that can be deployed"""

    type = models.IntegerField(
        choices=ERUType.choices,
        verbose_name=_("type"),
        default=0,
        help_text='<a target="_blank" href="/api/v2/erutype">Key/value pairs</a>',
    )
    units = models.IntegerField(verbose_name=_("units"), default=0)
    equipment_units = models.IntegerField(verbose_name=_("equipment units"), default=0)
    num_people_deployed = models.IntegerField(
        verbose_name=_("number of people deployed"), default=0, help_text=_("still not used in frontend")
    )
    # where deployed (none if available)
    deployed_to = models.ForeignKey(
        Country, verbose_name=_("country deployed to"), null=True, blank=True, on_delete=models.SET_NULL
    )
    event = models.ForeignKey(Event, verbose_name=_("event"), null=True, blank=True, on_delete=models.SET_NULL)
    appeal = models.ForeignKey(
        Appeal,
        verbose_name=_("appeal"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("still not used in frontend"),
    )
    # links to services
    eru_owner = models.ForeignKey(ERUOwner, verbose_name=_("owner"), on_delete=models.CASCADE)
    supporting_societies = models.CharField(
        verbose_name=_("supporting societies"),
        null=True,
        blank=True,
        max_length=500,
        help_text=_("still not used in frontend"),
    )
    start_date = models.DateTimeField(verbose_name=_("start date"), null=True, help_text=_("still not used in frontend"))
    end_date = models.DateTimeField(verbose_name=_("end date"), null=True, help_text=_("still not used in frontend"))
    available = models.BooleanField(verbose_name=_("available"), default=False)
    alert_date = models.DateTimeField(verbose_name=_("alert date"), null=True, help_text=_("still not used in frontend"))

    class Meta:
        verbose_name = _("Emergency Response Unit")
        verbose_name_plural = _("Emergency Response Units")

    def __str__(self):
        return self.get_type_display()


@reversion.register()
class PersonnelDeployment(models.Model):
    country_deployed_to = models.ForeignKey(Country, verbose_name=_("country deployed to"), on_delete=models.CASCADE)
    region_deployed_to = models.ForeignKey(
        Region, verbose_name=_("region deployed to"), null=True, on_delete=models.SET_NULL
    )
    event_deployed_to = models.ForeignKey(
        Event, verbose_name=_("event deployed to"), null=True, blank=True, on_delete=models.SET_NULL
    )
    appeal_deployed_to = models.ForeignKey(
        Appeal,
        verbose_name=_("appeal deployed to"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("still not used in frontend"),
    )
    alert_date = models.DateTimeField(verbose_name=_("alert date"), null=True, help_text=_("still not used in frontend"))
    exp_start_date = models.DateTimeField(
        verbose_name=_("expire start date"), null=True, help_text=_("still not used in frontend")
    )
    end_duration = models.CharField(
        verbose_name=_("end duration"), null=True, blank=True, max_length=100, help_text=_("still not used in frontend")
    )
    start_date = models.DateTimeField(verbose_name=_("start date"), null=True, help_text=_("still not used in frontend"))
    end_date = models.DateTimeField(verbose_name=_("end date"), null=True, help_text=_("still not used in frontend"))
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    previous_update = models.DateTimeField(verbose_name=_("previous update"), null=True, blank=True)
    comments = models.TextField(verbose_name=_("comments"), null=True, blank=True)
    is_molnix = models.BooleanField(default=False)  # Source is Molnix API

    class Meta:
        verbose_name = _("Personnel Deployment")
        verbose_name_plural = _("Personnel Deployments")

    def __str__(self):
        return "%s, %s" % (self.country_deployed_to, self.region_deployed_to)


@reversion.register()
class MolnixTagGroup(models.Model):
    molnix_id = models.IntegerField()
    name = models.CharField(max_length=255, verbose_name=_("name"))
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    is_deprecated = models.BooleanField(default=False, help_text=_("Is this a deprecated group?"))

    class Meta:
        verbose_name = _("Molnix Tag Group")
        verbose_name_plural = _("Molnix Tag Groups")

    def __str__(self):
        return self.name


@reversion.register()
class MolnixTag(models.Model):
    """
    We store tags from molnix in its own model, to make m2m relations
    from notifications.models.SurgeAlert and DeployedPerson
    """

    molnix_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(blank=True, max_length=512)
    color = models.CharField(max_length=6)
    tag_type = models.CharField(max_length=127)
    tag_category = models.CharField(null=True, max_length=127)
    groups = models.ManyToManyField(
        MolnixTagGroup,
        related_name="groups",
        blank=True,
    )

    def __str__(self):
        return self.name


@reversion.register()
class DeployedPerson(models.Model):
    start_date = models.DateTimeField(verbose_name=_("start date"), null=True)
    end_date = models.DateTimeField(verbose_name=_("end date"), null=True, db_index=True)
    name = models.CharField(verbose_name=_("name"), null=True, blank=True, max_length=255)
    role = models.CharField(verbose_name=_("role"), null=True, blank=True, max_length=512)

    class Meta:
        verbose_name = _("Deployed Person")
        verbose_name_plural = _("Deployed Persons")

    def __str__(self):
        return "%s - %s" % (self.name, self.role)


class Personnel(DeployedPerson):
    """
    Deployed personnel (connected to personneldeployment,
    which contains the details, date intervals etc.)
    """

    class TypeChoices(models.TextChoices):
        FACT = "fact", _("FACT")
        HEOP = "heop", _("HEOP")
        RDRT = "rdrt", _("RDRT")
        IFRC = "ifrc", _("IFRC")
        ERU = "eru", _("ERU HR")
        RR = "rr", _("Rapid Response")

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("ACTIVE")
        HIDDEN = "hidden", _("HIDDEN")
        DRAFT = "draft", _("DRAFT")
        DELETED = "deleted", _("DELETED")

    type = models.CharField(verbose_name=_("type"), choices=TypeChoices.choices, max_length=4)
    gender = models.CharField(verbose_name=_("gender"), null=True, blank=True, max_length=15)
    appraisal_received = models.BooleanField(default=False, verbose_name=_("appraisal received"))
    location = models.CharField(verbose_name=_("location"), blank=True, null=True, max_length=300)
    country_from = models.ForeignKey(
        Country, verbose_name=_("country from"), related_name="personnel_deployments", null=True, on_delete=models.SET_NULL
    )
    country_to = models.ForeignKey(
        Country, verbose_name=("country to"), related_name="personnel_deployments_to", null=True, on_delete=models.SET_NULL
    )
    deployment = models.ForeignKey(PersonnelDeployment, verbose_name=_("deployment"), on_delete=models.CASCADE)
    molnix_id = models.IntegerField(blank=True, null=True)
    molnix_tags = models.ManyToManyField(MolnixTag, blank=True)
    molnix_status = models.CharField(
        verbose_name=_("molnix status"), max_length=8, choices=StatusChoices.choices, default=StatusChoices.ACTIVE
    )
    is_active = models.BooleanField(default=True)  # Active in Molnix API
    surge_alert = models.ForeignKey(  # position_id in Molnix API
        'notifications.SurgeAlert',  # import as string to avoid circular import (MolnixTag)
        verbose_name=_("surge alert"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return "%s: %s - %s" % (self.type.upper(), self.name, self.role)

    class Meta:
        ordering = (
            "deployment",
            "country_to",
            "country_from",
            "molnix_id",
            "deployedperson_ptr_id",
        )
        verbose_name = _("Personnel")
        verbose_name_plural = _("Personnels")

    def get_tags_for_category(self, molnix_category):
        tags = self.molnix_tags.filter(tag_category=molnix_category).values("name")
        names = [tag["name"] for tag in tags]
        return ", ".join(names)


@reversion.register()
class PartnerSocietyActivities(models.Model):
    activity = models.CharField(verbose_name=_("activity"), max_length=50)

    def __str__(self):
        return self.activity

    class Meta:
        verbose_name = _("Partner society activity")
        verbose_name_plural = _("Partner society activities")


class PartnerSocietyDeployment(DeployedPerson):
    activity = models.ForeignKey(
        PartnerSocietyActivities,
        verbose_name=_("activity"),
        related_name="partner_societies",
        null=True,
        on_delete=models.CASCADE,
    )
    parent_society = models.ForeignKey(
        Country,
        verbose_name=_("parent society"),
        related_name="partner_society_members",
        null=True,
        on_delete=models.SET_NULL,
    )
    country_deployed_to = models.ForeignKey(
        Country,
        verbose_name=_("country deployed to"),
        related_name="country_partner_deployments",
        null=True,
        on_delete=models.SET_NULL,
    )
    district_deployed_to = models.ManyToManyField(District, verbose_name=_("district deployed to"))

    class Meta:
        verbose_name = _("Partner Society Deployment")
        verbose_name_plural = _("Partner Society Deployments")

    def __str__(self):
        return "%s deployment in %s" % (self.parent_society, self.country_deployed_to)


class ProgrammeTypes(models.IntegerChoices):
    BILATERAL = 0, _("Bilateral")
    MULTILATERAL = 1, _("Multilateral")
    DOMESTIC = 2, _("Domestic")


@reversion.register()
class Sector(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("title"))
    color = models.CharField(max_length=7, verbose_name=_("color"), null=True, blank=True)
    is_deprecated = models.BooleanField(default=False, help_text=_("Is this a deprecated sector?"))
    order = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Project Sector")
        verbose_name_plural = _("Project Sectors")

    def __str__(self):
        return self.title


@reversion.register()
class SectorTag(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("title"))
    color = models.CharField(max_length=7, verbose_name=_("color"), null=True, blank=True)
    is_deprecated = models.BooleanField(default=False, help_text=_("Is this a deprecated sector tag?"))
    order = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Project Sector Tag")
        verbose_name_plural = _("Project Sector Tags")

    def __str__(self):
        return self.title


class Statuses(models.IntegerChoices):
    PLANNED = 0, _("Planned")
    ONGOING = 1, _("Ongoing")
    COMPLETED = 2, _("Completed")


class OperationTypes(models.IntegerChoices):
    PROGRAMME = 0, _("Programme")
    EMERGENCY_OPERATION = 1, _("Emergency Operation")


@reversion.register()
class RegionalProject(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=100)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), auto_now=True)

    class Meta:
        verbose_name = _("Regional Project")
        verbose_name_plural = _("Regional Projects")

    def __str__(self):
        return self.name


# 3W
@reversion.register()
class Project(models.Model):
    modified_at = models.DateTimeField(verbose_name=_("modified at"), auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_modified_by",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )  # user who created this project
    # -- Reporting NS
    reporting_ns = models.ForeignKey(
        Country,
        verbose_name=_("reporting national society"),
        on_delete=models.CASCADE,
        related_name="ns_projects",
    )  # this is the national society that is reporting the project
    reporting_ns_contact_name = models.CharField(
        verbose_name=_("NS Contanct Information: Name"),
        max_length=255,
        blank=True,
        null=True,
    )
    reporting_ns_contact_role = models.CharField(
        verbose_name=_("NS Contanct Information: Role"),
        max_length=255,
        blank=True,
        null=True,
    )
    reporting_ns_contact_email = models.CharField(
        verbose_name=_("NS Contanct Information: Email"),
        max_length=255,
        blank=True,
        null=True,
    )
    project_country = models.ForeignKey(
        Country,
        verbose_name=_("country"),
        on_delete=models.CASCADE,
        null=True,  # NOTE: Added due to migrations issue
        related_name="projects",
    )  # this is the country where the project is actually taking place
    project_districts = models.ManyToManyField(
        District,
        verbose_name=_("districts"),
        blank=True,
    )  # this is the district where the project is actually taking place
    project_admin2 = models.ManyToManyField(
        Admin2,
        verbose_name=_("admin2"),
        blank=True,
    )
    event = models.ForeignKey(
        Event,
        verbose_name=_("event"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )  # this is the current operation
    dtype = models.ForeignKey(
        DisasterType, verbose_name=_("disaster type"), null=True, blank=True, on_delete=models.SET_NULL
    )
    name = models.TextField(verbose_name=_("name"))
    description = HTMLField(verbose_name=_("description"), blank=True, default="")
    document = models.ForeignKey(
        GeneralDocument, verbose_name=_("linked document"), null=True, blank=True, on_delete=models.SET_NULL
    )
    programme_type = models.IntegerField(
        choices=ProgrammeTypes.choices,
        default=0,
        verbose_name=_("programme type"),
        help_text='<a target="_blank" href="/api/v2/programmetype">Key/value pairs</a>',
    )
    primary_sector = models.ForeignKey(
        Sector,
        verbose_name=_("sector"),
        on_delete=models.PROTECT,
    )
    secondary_sectors = models.ManyToManyField(
        SectorTag,
        related_name="tags",
        blank=True,
    )
    operation_type = models.IntegerField(
        choices=OperationTypes.choices,
        default=0,
        verbose_name=_("operation type"),
        help_text='<a target="_blank" href="/api/v2/operationtype">Key/value pairs</a>',
    )
    start_date = models.DateField(verbose_name=_("start date"))
    end_date = models.DateField(verbose_name=_("end date"))
    budget_amount = models.IntegerField(verbose_name=_("budget amount"), null=True, blank=True)
    actual_expenditure = models.IntegerField(verbose_name=_("actual expenditure"), null=True, blank=True)
    status = models.IntegerField(
        choices=Statuses.choices,
        default=0,
        verbose_name=_("status"),
        help_text='<a target="_blank" href="/api/v2/projectstatus">Key/value pairs</a>',
    )

    # Target Metric
    target_male = models.IntegerField(verbose_name=_("target male"), null=True, blank=True)
    target_female = models.IntegerField(verbose_name=_("target female"), null=True, blank=True)
    target_other = models.IntegerField(verbose_name=_("target other"), null=True, blank=True)
    target_total = models.IntegerField(verbose_name=_("target total"), null=True, blank=True)

    # Reached Metric
    reached_male = models.IntegerField(verbose_name=_("reached male"), null=True, blank=True)
    reached_female = models.IntegerField(verbose_name=_("reached female"), null=True, blank=True)
    reached_other = models.IntegerField(verbose_name=_("reached other"), null=True, blank=True)
    reached_total = models.IntegerField(verbose_name=_("reached total"), null=True, blank=True)

    regional_project = models.ForeignKey(
        RegionalProject, verbose_name=_("regional project"), null=True, blank=True, on_delete=models.SET_NULL
    )
    visibility = models.CharField(
        max_length=32,
        verbose_name=_("visibility"),
        choices=VisibilityCharChoices.choices,
        default=VisibilityCharChoices.PUBLIC,
    )

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __str__(self):
        if self.reporting_ns is None:
            postfix = None
        else:
            postfix = self.reporting_ns.society_name
        return "%s (%s)" % (self.name, postfix)

    def save(self, *args, **kwargs):
        if hasattr(self, "annual_split_detail"):
            # NO NEED: and self.annual_split_detail – because we want to get here in case of [] also:
            if hasattr(self, "is_annual_report") and self.is_annual_report:
                arrivingIds = [asd["id"] for asd in self.annual_split_detail]
                # Remove the records frontend has not sent, due to frontend-wise row removal:
                AnnualSplit.objects.filter(project_id=self.id).exclude(id__in=arrivingIds).delete()
                for split in self.annual_split_detail:
                    annual_split, created = AnnualSplit.objects.get_or_create(pk=split["id"], project_id=self.id)
                    annual_split.year = split["year"] if "year" in split else None
                    annual_split.budget_amount = split["budget_amount"] if "budget_amount" in split else None
                    annual_split.target_male = split["target_male"] if "target_male" in split else None
                    annual_split.target_female = split["target_female"] if "target_female" in split else None
                    annual_split.target_other = split["target_other"] if "target_other" in split else None
                    annual_split.target_total = split["target_total"] if "target_total" in split else None
                    annual_split.reached_male = split["reached_male"] if "reached_male" in split else None
                    annual_split.reached_female = split["reached_female"] if "reached_female" in split else None
                    annual_split.reached_other = split["reached_other"] if "reached_other" in split else None
                    annual_split.reached_total = split["reached_total"] if "reached_total" in split else None
                    annual_split.save()
            else:
                AnnualSplit.objects.filter(project_id=self.id).delete()

        # Automatically assign status according to the start_date and end_date
        # Cronjob will change the status automatically in future
        now = timezone.now().date()
        if self.start_date > now:
            self.status = Statuses.PLANNED
        elif self.start_date <= now <= self.end_date:
            self.status = Statuses.ONGOING
        else:
            self.status = Statuses.COMPLETED
        return super().save(*args, **kwargs)

    # FIXME: Is this used?
    @staticmethod
    def get_for(user, queryset=None):
        countries_qs = (
            UserCountry.objects.filter(user=user)
            .values("country")
            .union(Profile.objects.filter(user=user).values("country"))
        )
        return queryset.exclude(
            Q(visibility=VisibilityCharChoices.IFRC_NS)
            & ~Q(project_country__in=countries_qs)
            & ~Q(reporting_ns__in=countries_qs)
        )


# FIXME | Something like this would be helpful, but not this way. Hint:
#    def get_primary_sector_display(self):
#        return 'primary_sector__title'
#
#    def get_secondary_sectors_display(self):
#        return 'secondary_sectors__title'


@reversion.register(follow=('project',))
class AnnualSplit(models.Model):
    """Annual split for Project"""

    project = models.ForeignKey(Project, verbose_name=_("project"), related_name="annual_splits", on_delete=models.CASCADE)
    year = models.IntegerField(verbose_name=_("year"), null=True, blank=True)
    budget_amount = models.IntegerField(verbose_name=_("amount"), null=True, blank=True)
    target_male = models.IntegerField(verbose_name=_("target male"), null=True, blank=True)
    target_female = models.IntegerField(verbose_name=_("target female"), null=True, blank=True)
    target_other = models.IntegerField(verbose_name=_("target other"), null=True, blank=True)
    target_total = models.IntegerField(verbose_name=_("target total"), null=True, blank=True)
    reached_male = models.IntegerField(verbose_name=_("reached male"), null=True, blank=True)
    reached_female = models.IntegerField(verbose_name=_("reached female"), null=True, blank=True)
    reached_other = models.IntegerField(verbose_name=_("reached other"), null=True, blank=True)
    reached_total = models.IntegerField(verbose_name=_("reached total"), null=True, blank=True)

    class Meta:
        verbose_name = _("Annual Split")
        verbose_name_plural = _("Annual Splits")

    def __str__(self):
        return "%s: %s %s | %s %s" % (
            str(self.project_id),
            str(self.year),
            str(self.budget_amount),
            str(self.target_male),
            str(self.reached_male),
        )


@reversion.register()
class ProjectImport(models.Model):
    """
    Track Project Imports (For Django Admin Panel)
    """

    class ProjImpStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        SUCCESS = "success", _("Success")
        FAILURE = "failure", _("Failure")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
    )  # user who created this project import
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    projects_created = models.ManyToManyField(Project, verbose_name=_("projects created"))
    message = models.TextField(verbose_name=_("message"))
    status = models.CharField(
        verbose_name=_("status"), max_length=10, choices=ProjImpStatus.choices, default=ProjImpStatus.PENDING
    )
    file = models.FileField(verbose_name=_("file"), upload_to="project-imports/")

    class Meta:
        verbose_name = _("Project Import")
        verbose_name_plural = _("Projects Import")

    def __str__(self):
        return f"Project Import {self.get_status_display()}:{self.created_at}"


# -------------- Emergency 3W [Start]
@reversion.register()
class EmergencyProject(models.Model):
    class ActivityLead(models.TextChoices):
        NATIONAL_SOCIETY = "national_society", _("National Society")
        DEPLOYED_ERU = "deployed_eru", _("Deployed ERU")

    class ActivityStatus(models.TextChoices):
        ON_GOING = "on_going", _("Ongoing")
        COMPLETE = "complete", _("Complete")
        PLANNED = "planned", _("Planned")

    title = models.CharField(max_length=255, verbose_name=_("title"))
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    event = models.ForeignKey(
        Event, verbose_name=_("Event"), on_delete=models.CASCADE, related_name="+"
    )  # this is the current operation
    districts = models.ManyToManyField(
        District,
        verbose_name=_("Districts"),
        related_name="+",
        blank=True,
    )  # this is the district where the project is actually taking place
    admin2 = models.ManyToManyField(
        Admin2,
        verbose_name=_("admin2"),
        blank=True,
    )  # admin2 of the district where the project is actually taking place
    # Who is conducting the Activity
    activity_lead = models.CharField(
        max_length=30,
        verbose_name=_("Activity lead"),
        choices=ActivityLead.choices,
    )
    # -- Reporting NS
    reporting_ns = models.ForeignKey(
        Country,
        verbose_name=_("Reporting national society"),
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    reporting_ns_contact_name = models.CharField(
        verbose_name=_("NS Contact Information: Name"),
        max_length=255,
        blank=True,
        null=True,
    )
    reporting_ns_contact_role = models.CharField(
        verbose_name=_("NS Contact Information: Role"),
        max_length=255,
        blank=True,
        null=True,
    )
    reporting_ns_contact_email = models.CharField(
        verbose_name=_("NS Contact Information: Email"),
        max_length=255,
        blank=True,
        null=True,
    )
    # -- Deployed ERU
    deployed_eru = models.ForeignKey(
        ERU,
        verbose_name=_("Deployed ERU"),
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    start_date = models.DateField(
        verbose_name=_("Start Date"),
        blank=False,
        null=False,
    )
    end_date = models.DateField(
        verbose_name=_("End Date"),
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=40,
        choices=ActivityStatus.choices,
        default=ActivityStatus.ON_GOING,
    )
    country = models.ForeignKey(
        Country,
        verbose_name=_("Country"),
        on_delete=models.CASCADE,
        related_name="+",
    )  # Country to be among the country in event
    visibility = models.CharField(
        max_length=32,
        verbose_name=_("visibility"),
        choices=VisibilityCharChoices.choices,
        default=VisibilityCharChoices.PUBLIC,
    )

    def __str__(self):
        return self.title


@reversion.register()
class EmergencyProjectActivitySector(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("title"))
    order = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.title


@reversion.register()
class EmergencyProjectActivityAction(models.Model):
    sector = models.ForeignKey(
        EmergencyProjectActivitySector,
        verbose_name=_("sector"),
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=255, verbose_name=_("title"))
    order = models.SmallIntegerField(default=0)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    is_cash_type = models.BooleanField(default=False, verbose_name=_("is_cash_type"))
    has_location = models.BooleanField(default=False, verbose_name=_("has location"))

    def __str__(self):
        return self.title


@reversion.register()
class EmergencyProjectActivityActionSupply(models.Model):
    action = models.ForeignKey(
        EmergencyProjectActivityAction,
        verbose_name=_("action"),
        related_name="supplies",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=255, verbose_name=_("title"))
    order = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.title


@reversion.register()
class EmergencyProjectActivityLocation(models.Model):
    # Location Data
    latitude = models.FloatField(verbose_name=_("latitude"))
    longitude = models.FloatField(verbose_name=_("longitude"))
    description = models.TextField(verbose_name=_("location description"))

    def __str__(self):
        return f"{self.latitude} - {self.longitude}"


@reversion.register(follow=('project',))
class EmergencyProjectActivity(models.Model):
    class PeopleHouseholds(models.TextChoices):
        PEOPLE = "people", _("People")
        HOUSEHOLDS = "households", _("Households")

    sector = models.ForeignKey(
        EmergencyProjectActivitySector,
        verbose_name=_("sector"),
        on_delete=models.CASCADE,
    )
    action = models.ForeignKey(
        EmergencyProjectActivityAction,
        verbose_name=_("action"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    project = models.ForeignKey(
        EmergencyProject,
        verbose_name=_("emergency project/3W"),
        on_delete=models.CASCADE,
        related_name="activities",
    )
    is_simplified_report = models.BooleanField(verbose_name=_("is_simplified_report"), default=True)
    is_disaggregated_for_disabled = models.BooleanField(
        verbose_name=_("Is disaggregated for disabled"), null=True, blank=True
    )
    has_no_data_on_people_reached = models.BooleanField(
        verbose_name=_("Has no data on people reached"), null=True, blank=True
    )
    # Metrics
    people_households = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=PeopleHouseholds.choices,
        verbose_name=_("People Households"),
    )
    household_count = models.IntegerField(verbose_name=_("Household"), null=True, blank=True)
    # if sector.is_cash_type is True
    amount = models.IntegerField(verbose_name=_("Amount"), null=True, blank=True)
    beneficiaries_count = models.IntegerField(verbose_name=_("Beneficiaries Count"), null=True, blank=True)

    item_count = models.IntegerField(verbose_name=_("Item"), null=True, blank=True)

    people_count = models.IntegerField(verbose_name=_("People"), null=True, blank=True)
    male_count = models.IntegerField(verbose_name=_("Men"), null=True, blank=True)
    female_count = models.IntegerField(verbose_name=_("Female"), null=True, blank=True)
    # -- Age group
    male_unknown_age_count = models.IntegerField(verbose_name=_("Male Unknown Age"), null=True, blank=True)
    female_unknown_age_count = models.IntegerField(verbose_name=_("Female Unknown Age"), null=True, blank=True)
    other_unknown_age_count = models.IntegerField(verbose_name=_("Other Unknown Age"), null=True, blank=True)
    # -- When is_simplified_report is False
    male_0_1_count = models.IntegerField(verbose_name=_("Boys 0-1"), null=True, blank=True)
    male_2_5_count = models.IntegerField(verbose_name=_("Boys 2-5"), null=True, blank=True)
    male_6_12_count = models.IntegerField(verbose_name=_("Boys 6-12"), null=True, blank=True)
    male_13_17_count = models.IntegerField(verbose_name=_("Boys 13-17"), null=True, blank=True)
    male_18_59_count = models.IntegerField(verbose_name=_("Men 18-29"), null=True, blank=True)
    male_60_plus_count = models.IntegerField(verbose_name=_("Older Men 60+"), null=True, blank=True)
    female_0_1_count = models.IntegerField(verbose_name=_("Girls 0-1"), null=True, blank=True)
    female_2_5_count = models.IntegerField(verbose_name=_("Girls 2-5"), null=True, blank=True)
    female_6_12_count = models.IntegerField(verbose_name=_("Girls 6-12"), null=True, blank=True)
    female_13_17_count = models.IntegerField(verbose_name=_("Girls 13-17"), null=True, blank=True)
    female_18_59_count = models.IntegerField(verbose_name=_("Women 18-29"), null=True, blank=True)
    female_60_plus_count = models.IntegerField(verbose_name=_("Older Women 60+"), null=True, blank=True)
    other_0_1_count = models.IntegerField(verbose_name=_("Others/Unknown 0-1"), null=True, blank=True)
    other_2_5_count = models.IntegerField(verbose_name=_("Others/Unknown 2-5"), null=True, blank=True)
    other_6_12_count = models.IntegerField(verbose_name=_("Others/Unknown 6-12"), null=True, blank=True)
    other_13_17_count = models.IntegerField(verbose_name=_("Others/Unknown 13-17"), null=True, blank=True)
    other_18_59_count = models.IntegerField(verbose_name=_("Others/Unknown 18-29"), null=True, blank=True)
    other_60_plus_count = models.IntegerField(verbose_name=_("Others/Unknown 60+"), null=True, blank=True)
    # -- When is_disaggregated_for_disabled is True
    disabled_male_0_1_count = models.IntegerField(verbose_name=_("Disabled Boys 0-1"), null=True, blank=True)
    disabled_male_2_5_count = models.IntegerField(verbose_name=_("Disabled Boys 2-5"), null=True, blank=True)
    disabled_male_6_12_count = models.IntegerField(verbose_name=_("Disabled Boys 6-12"), null=True, blank=True)
    disabled_male_13_17_count = models.IntegerField(verbose_name=_("Disabled Boys 13-17"), null=True, blank=True)
    disabled_male_18_59_count = models.IntegerField(verbose_name=_("Disabled Men 18-29"), null=True, blank=True)
    disabled_male_60_plus_count = models.IntegerField(verbose_name=_("Disabled Older Men 60+"), null=True, blank=True)
    disabled_female_0_1_count = models.IntegerField(verbose_name=_("Disabled Girls 0-1"), null=True, blank=True)
    disabled_female_2_5_count = models.IntegerField(verbose_name=_("Disabled Girls 2-5"), null=True, blank=True)
    disabled_female_6_12_count = models.IntegerField(verbose_name=_("Disabled Girls 6-12"), null=True, blank=True)
    disabled_female_13_17_count = models.IntegerField(verbose_name=_("Disabled Girls 13-17"), null=True, blank=True)
    disabled_female_18_59_count = models.IntegerField(verbose_name=_("Disabled Women 18-29"), null=True, blank=True)
    disabled_female_60_plus_count = models.IntegerField(verbose_name=_("Disabled Older Women 60+"), null=True, blank=True)
    disabled_other_0_1_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 0-1"), null=True, blank=True)
    disabled_other_2_5_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 2-5"), null=True, blank=True)
    disabled_other_6_12_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 6-12"), null=True, blank=True)
    disabled_other_13_17_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 13-17"), null=True, blank=True)
    disabled_other_18_59_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 18-29"), null=True, blank=True)
    disabled_other_60_plus_count = models.IntegerField(verbose_name=_("Disabled Others/Unknown 60+"), null=True, blank=True)
    disabled_male_unknown_age_count = models.IntegerField(verbose_name=_("Disabled Male Unknown Age"), null=True, blank=True)
    disabled_female_unknown_age_count = models.IntegerField(
        verbose_name=_("Disabled Female Unknown Age"), null=True, blank=True
    )
    disabled_other_unknown_age_count = models.IntegerField(
        verbose_name=_("Disabled Other Unknown Age"), null=True, blank=True
    )

    # More Details
    details = models.TextField(verbose_name=_("details"), blank=True, null=True)
    supplies = JSONField(verbose_name=_("supplies"), default=dict, blank=True)  # key: count (key: System defined id)
    # Custom action/supplies
    custom_action = models.CharField(verbose_name=_("custom_action"), max_length=255, blank=True, null=True)
    custom_supplies = JSONField(verbose_name=_("custom supplies"), default=dict, blank=True)  # key: count (key: User defined)
    # point details
    # point_count to be used if is_simplified_report is True
    point_count = models.IntegerField(verbose_name=_("Point Count"), null=True, blank=True)
    # points to be used if is_simplified_report is False
    points = models.ManyToManyField(EmergencyProjectActivityLocation, verbose_name=_("Points"), blank=True)


# -------------- Emergency 3W [END]
@reversion.register()
class ERUReadiness(models.Model):
    """ERU Readiness concerning personnel and equipment"""

    national_society = models.ForeignKey(
        Country, verbose_name=_("national society"), null=True, blank=True, on_delete=models.SET_NULL
    )
    ERU_type = models.IntegerField(choices=ERUType.choices, verbose_name=_("ERU type"), default=0)
    is_personnel = models.BooleanField(verbose_name=_("is personnel?"), default=False)
    is_equipment = models.BooleanField(verbose_name=_("is equipment?"), default=False)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    class Meta:
        ordering = (
            "updated_at",
            "national_society",
        )
        verbose_name = _("ERU Readiness")
        verbose_name_plural = _("NS-es ERU Readiness")

    def __str__(self):
        if self.national_society is None:
            name = None
        else:
            name = self.national_society
        return f"{self.get_ERU_type_display()} ({name})"


###############################################################################
####################### Deprecated tables ##################################### noqa: E266
# https://github.com/IFRCGo/go-frontend/issues/335
# NOTE: Translation is skipped for Deprecated tables
###############################################################################


class Heop(models.Model):
    """A deployment of a head officer"""

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)

    person = models.CharField(null=True, blank=True, max_length=100)
    role = models.CharField(default="HeOps", null=True, blank=True, max_length=32)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "HeOp"
        verbose_name_plural = "HeOps"

    def __str__(self):
        return "%s (%s) %s - %s" % (
            self.person,
            self.country,
            datetime.strftime(self.start_date, DATE_FORMAT),
            datetime.strftime(self.end_date, DATE_FORMAT),
        )


class Fact(models.Model):
    """A FACT resource"""

    start_date = models.DateTimeField(null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return "%s %s" % (self.country, datetime.strftime(self.start_date, DATE_FORMAT))

    class Meta:
        verbose_name = "FACT"
        verbose_name_plural = "FACTs"


class Rdrt(models.Model):
    """An RDRT/RIT resource"""

    start_date = models.DateTimeField(null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return "%s %s" % (self.country, datetime.strftime(self.start_date, DATE_FORMAT))

    class Meta:
        verbose_name = "RDRT/RIT"
        verbose_name_plural = "RDRTs/RITs"


class FactPerson(DeployedPerson):
    society_deployed_from = models.CharField(null=True, blank=True, max_length=100)
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "FACT Person"
        verbose_name_plural = "FACT People"


class RdrtPerson(DeployedPerson):
    society_deployed_from = models.CharField(null=True, blank=True, max_length=100)
    rdrt = models.ForeignKey(Rdrt, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "RDRT/RIT Person"
        verbose_name_plural = "RDRT/RIT People"
