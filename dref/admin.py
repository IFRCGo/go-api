from django.contrib import admin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    DrefCountryDistrict,
    DrefFile
)


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    pass


@admin.register(PlannedIntervention)
class PlannedInterventionAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(IdentifiedNeed)
class IdentifiedNeedAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(NationalSocietyAction)
class NationalSocietyActiondAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


class DrefCountryDistrictAdminInline(admin.TabularInline):
    model = DrefCountryDistrict
    extra = 0


@admin.register(Dref)
class DrefAdmin(TranslationAdmin, admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'national_society', 'disaster_type',
                    'ns_request_date', 'submission_to_geneva', 'status')
    inlines = [DrefCountryDistrictAdminInline]
    autocomplete_fields = ('planned_interventions', 'needs_identified', 'national_society_actions')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'planned_interventions', 'needs_identified', 'national_society_actions')
