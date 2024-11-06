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
                    "fdrs_population",
                    "fdrs_population_data_year",
                    "fdrs_urban_population",
                    "fdrs_urban_population_data_year",
                    "fdrs_gdp",
                    "fdrs_gdp_data_year",
                    "fdrs_gnipc",
                    "fdrs_gnipc_data_year",
                    "fdrs_poverty",
                    "fdrs_poverty_data_year",
                    "fdrs_life_expectancy",
                    "fdrs_life_expectancy_data_year",
                    "fdrs_literacy",
                    "fdrs_literacy_data_year",
                )
            },
        ),
        (
            _("NATIONAL SOCIETY INDICATORS (SOURCE: FDRS)"),
            {
                "fields": (
                    "fdrs_income",
                    "fdrs_income_data_year",
                    "fdrs_expenditures",
                    "fdrs_expenditures_data_year",
                    "fdrs_volunteer_total",
                    "fdrs_volunteer_data_year",
                    "fdrs_staff_total",
                    "fdrs_staff_data_year",
                    "fdrs_trained_in_first_aid",
                    "fdrs_trained_in_first_aid_data_year",
                    "fdrs_branches",
                    "fdrs_branches_data_year",
                ),
            },
        ),
        (_("KEY CLIMATE EVENT"), {"fields": ("avg_temperature", "avg_rainfall_precipitation", "rainy_season")}),
        (
            _("World bank"),
            {
                "fields": (
                    "world_bank_population",
                    "world_bank_population_year",
                    "world_bank_population_above_age_65",
                    "world_bank_population_above_age_65_year",
                    "world_bank_population_age_14",
                    "world_bank_population_age_14_year",
                    "world_bank_urban_population_percentage",
                    "world_bank_urban_population_percentage_year",
                    "world_bank_gdp",
                    "world_bank_gdp_year",
                    "world_bank_gni",
                    "world_bank_gni_year",
                    "world_bank_gender_equality_index",
                    "world_bank_gender_equality_index_year",
                    "world_bank_life_expectancy",
                    "world_bank_life_expectancy_year",
                    "world_bank_literacy_rate",
                    "world_bank_literacy_rate_year",
                    "world_bank_poverty_rate",
                    "world_bank_poverty_rate_year",
                    "world_bank_gni_capita",
                    "world_bank_gni_capita_year",
                )
            },
        ),
    )
