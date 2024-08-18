from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .forms import CountryOverviewForm, SeasonalCalenderForm
from .models import (
    AcapsSeasonalCalender,
    CountryKeyClimate,
    CountryOverview,
    ExternalSource,
    FDRSAnnualIncome,
    FDRSIncome,
    KeyClimateEvent,
    KeyDocument,
    KeyDocumentGroup,
    Month,
    SeasonalCalender,
    SocialEvent,
)

admin.site.register([CountryKeyClimate, KeyDocumentGroup])


class SocialEventInline(admin.TabularInline):
    model = SocialEvent


class KeyClimateEventByInline(admin.TabularInline):
    model = KeyClimateEvent
    max_num = len(Month.CHOICES)


class SeasonalCalenderInine(admin.TabularInline):
    model = SeasonalCalender
    form = SeasonalCalenderForm


class KeyDocumentInine(admin.TabularInline):
    model = KeyDocument


class ExternalSourceInine(admin.TabularInline):
    model = ExternalSource


class AcapsSeasonalCalenderInline(admin.TabularInline):
    model = AcapsSeasonalCalender


class FDRSIncomeInline(admin.TabularInline):
    model = FDRSIncome


class FDRSAnnualIncomeInline(admin.TabularInline):
    model = FDRSAnnualIncome


@admin.register(CountryOverview)
class CountryOverviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ("country",)
    search_fields = ("country__name",)
    list_display = ("country",)
    inlines = [
        SocialEventInline,
        KeyClimateEventByInline,
        SeasonalCalenderInine,
        KeyDocumentInine,
        ExternalSourceInine,
        AcapsSeasonalCalenderInline,
        FDRSIncomeInline,
        FDRSAnnualIncomeInline,
    ]
    form = CountryOverviewForm
    # TODO: Add all of the fields
    fieldsets = (
        (None, {"fields": ("country",)}),
        (
            _("COUNTRY KEY INDICATORS (SOURCE: FDRS)"),
            {
                "fields": (
                    "population",
                    "urban_population",
                    "gdp",
                    "gnipc",
                    "poverty",
                    "life_expectancy",
                    "literacy",
                )
            },
        ),
        (
            _("NATIONAL SOCIETY INDICATORS (SOURCE: FDRS)"),
            {
                "fields": ("income", "expenditures", "volunteers", "trained_in_first_aid", "branches"),
            },
        ),
        (_("KEY CLIMATE EVENT"), {"fields": ("avg_temperature", "avg_rainfall_precipitation", "rainy_season")}),
        (
            _("World bank"),
            {
                "fields": (
                    "world_bank_population",
                    "calculated_world_bank_population_year",
                    "world_bank_population_above_age_65",
                    "calculated_world_bank_population_above_age_65_year",
                    "world_bank_population_age_14",
                    "calculated_world_bank_population_age_14_year",
                    "world_bank_urban_population_percentage",
                    "calculated_world_bank_urban_population_percentage_year",
                    "world_bank_gdp",
                    "calculated_world_bank_gdp_year",
                    "world_bank_gni",
                    "calculated_world_bank_gni_year",
                    "world_bank_gender_inequality_index",
                    "calculated_world_bank_gender_inequality_index_year",
                    "world_bank_life_expectancy",
                    "calculated_world_bank_life_expectancy_year",
                    "world_bank_literacy_rate",
                    "calculated_world_bank_literacy_rate_year",
                    "world_bank_poverty_rate",
                    "calculated_world_bank_poverty_rate_year",
                    "world_bank_gni_capita",
                    "calculated_world_bank_gni_capita_year",
                )
            },
        ),
    )
