from django.contrib import admin

from country_plan.models import (
    CountryPlan,
    DataImport,
    MembershipCoordination,
    StrategicPriority,
)


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    readonly_fields = ("errors",)

    change_form_template = "admin/countryplan_change_form.html"
    change_list_template = "admin/countryplan_change_list.html"


@admin.register(CountryPlan)
class CountryPlanAdmin(admin.ModelAdmin):
    autocomplete_fields = ("country",)
    search_fields = ("country__name",)
    list_filter = ("is_publish",)

    change_form_template = "admin/countryplan_change_form.html"
    change_list_template = "admin/countryplan_change_list.html"


@admin.register(StrategicPriority)
class StrategicPriorityAdmin(admin.ModelAdmin):
    list_display = ("country_plan", "type", "people_targeted")
    autocomplete_fields = ("country_plan",)


@admin.register(MembershipCoordination)
class MembershipCoordinationAdmin(admin.ModelAdmin):
    list_display = ("country_plan", "national_society", "sector")
    search_fields = ("sector",)
    autocomplete_fields = ("national_society", "country_plan")
