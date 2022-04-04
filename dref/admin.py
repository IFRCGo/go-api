from django.contrib import admin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    DrefCountryDistrict,
    DrefFile,
    DrefOperationalUpdate
)


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ('file',)


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
    autocomplete_fields = ('country', 'district',)


@admin.register(Dref)
class DrefAdmin(TranslationAdmin, admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'national_society', 'disaster_type',
                    'ns_request_date', 'submission_to_geneva', 'status',)
    inlines = [DrefCountryDistrictAdminInline]
    autocomplete_fields = (
        'planned_interventions',
        'needs_identified',
        'national_society_actions',
        'national_society',
        'disaster_type',
        'users',
        'event_map',
        'images',
        'budget_file',
        'cover_image',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'planned_interventions',
            'needs_identified',
            'national_society_actions',
            'users'
        )


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'planned_interventions',
        'needs_identified',
        'national_society_actions',
        'national_society',
        'disaster_type',
        'images',
        'district',
    )
