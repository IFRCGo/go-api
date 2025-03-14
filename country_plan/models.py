from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api.models import Country
from main.fields import SecureFileField


def file_upload_to(instance, filename):
    date_str = timezone.now().strftime("%Y-%m-%d-%H-%M-%S")
    return f"country-plan-excel-files/{date_str}/{filename}"


def pdf_upload_to(instance, filename):
    date_str = timezone.now().strftime("%Y-%m-%d-%H-%M-%S")
    return f"country-plan-pdf/{date_str}/{filename}"


class CountryPlanAbstract(models.Model):
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created By"),
        blank=True,
        null=True,
        related_name="%(class)s_created_by",
        on_delete=models.SET_NULL,
        editable=False,
    )
    created_at = models.DateTimeField(verbose_name=_("Created at"), auto_now_add=True)
    updated_by = models.ForeignKey(
        User,
        verbose_name=_("Updated by"),
        blank=True,
        null=True,
        related_name="%(class)s_updated_by",
        on_delete=models.SET_NULL,
        editable=False,
    )
    updated_at = models.DateTimeField(verbose_name=_("Updated at"), auto_now=True)

    class Meta:
        abstract = True


class DataImport(CountryPlanAbstract):
    file = models.FileField(verbose_name=_("EXCEL file"), upload_to=file_upload_to)
    errors = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        from .tasks import process_data_import

        new = False
        if self.pk is None:
            new = True
        super().save(*args, **kwargs)
        if new:
            transaction.on_commit(lambda: process_data_import.delay(self.pk))


class CountryPlan(CountryPlanAbstract):
    country = models.OneToOneField(Country, on_delete=models.CASCADE, related_name="country_plan", primary_key=True)
    internal_plan_file = SecureFileField(
        verbose_name=_("Internal Plan"),
        upload_to=pdf_upload_to,
        validators=[FileExtensionValidator(["pdf"])],
        blank=True,
        null=True,
    )
    internal_plan_url = models.URLField(verbose_name=_("internal_plan_url"), blank=True, null=True)
    public_plan_file = models.FileField(
        verbose_name=_("Country Plan"),
        validators=[FileExtensionValidator(["pdf"])],
        upload_to=pdf_upload_to,
        blank=True,
        null=True,
    )
    public_plan_url = models.URLField(verbose_name=_("public_plan_url"), blank=True, null=True)
    requested_amount = models.FloatField(verbose_name=_("Requested Amount"), blank=True, null=True)
    people_targeted = models.IntegerField(verbose_name=_("People Targeted"), blank=True, null=True)
    is_publish = models.BooleanField(default=False, verbose_name=_("Published"))

    # NOTE: Used to sync with Appeal API (ingest_country_plan_file.py for more info)
    public_plan_inserted_date = models.DateTimeField(blank=True, null=True)
    internal_plan_inserted_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.country}"

    def full_country_plan_mc(self):
        all_mc = list(self.country_plan_mc.all())
        mc_by_ns_sector = {(mc.national_society_id, mc.sector): mc for mc in all_mc}
        ns_ids = set([mc.national_society_id for mc in all_mc])
        return [
            (
                mc_by_ns_sector.get((nc_id, sector))
                or MembershipCoordination(
                    national_society_id=nc_id,
                    sector=sector,
                )
            )
            for nc_id in ns_ids
            for sector, _ in MembershipCoordination.Sector.choices
        ]


class StrategicPriority(models.Model):
    class Type(models.TextChoices):
        ONGOING_EMERGENCY_OPERATIONS = "ongoing_emergency_operations", _("Ongoing emergency operations")
        CLIMATE_AND_ENVIRONMENT = "climate_and_environment", _("Climate and environment")
        EVOLVING_CRISIS_AND_DISASTERS = "disasters_and_crisis", _("Disasters and crisis")
        HEALTH_AND_WELLBEING = "health_and_wellbeing", _("Health and wellbeing")
        MIGRATION_AND_DISPLACEMENT = "migration_and_displacement", _("Migration and displacement")
        VALUE_POWER_AND_INCLUSION = "value_power_and_inclusion", _("Values, power and inclusion")

    country_plan = models.ForeignKey(
        CountryPlan,
        on_delete=models.CASCADE,
        verbose_name=_("Country Plan"),
        related_name="country_plan_sp",
    )
    type = models.CharField(max_length=100, choices=Type.choices, verbose_name=_("Type"))
    funding_requirement = models.FloatField(verbose_name=_("Funding Requirement"), blank=True, null=True)
    people_targeted = models.IntegerField(verbose_name=_("People Targeted"), blank=True, null=True)

    class Meta:
        unique_together = ("country_plan", "type")

    def __str__(self):
        return f"{self.type}"


class MembershipCoordination(models.Model):
    class Sector(models.TextChoices):
        CLIMATE = "climate", _("Climate")
        CRISIS = "crisis", _("Crisis")
        HEALTH = "health", _("Health")
        MIGRATION = "migration", _("Migration")
        INCLUSION = "inclusion", _("Inclusion")
        ENABLING_FUNCTIONS = "enabling_functions", _("Enabling functions")

    country_plan = models.ForeignKey(
        CountryPlan,
        on_delete=models.CASCADE,
        verbose_name=_("Country Plan"),
        related_name="country_plan_mc",
    )
    sector = models.CharField(max_length=100, choices=Sector.choices, verbose_name=_("Sector"))
    national_society = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="national_society_mc")
    has_coordination = models.BooleanField(default=False)

    class Meta:
        unique_together = ("country_plan", "national_society", "sector")

    def __str__(self):
        return f"{self.national_society.iso3}-{self.sector}"
