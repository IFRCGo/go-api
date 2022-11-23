from django.contrib import admin

from country_plan.models import (
    CountryPlan,
    DataImport,
    StrategicPriority,
    MembershipCoordination
)
# Register your models here.


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    pass


@admin.register(CountryPlan)
class CountryPlanAdmin(admin.ModelAdmin):
    autocomplete_fields = ('country',)
    search_fields = ('country',)


@admin.register(StrategicPriority)
class StrategicPriorityAdmin(admin.ModelAdmin):
    list_display = ('country_plan', 'sp_name', 'people_targeted')
    autocomplete_fields = ('country_plan',)


@admin.register(MembershipCoordination)
class MembershipCoordinationAdmin(admin.ModelAdmin):
    list_display = ('country_plan', 'national_society', 'strategic_priority')
    search_fields = ('strategic_priority',)
    autocomplete_fields = ('national_society', 'country_plan')
