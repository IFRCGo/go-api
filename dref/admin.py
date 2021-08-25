from django.contrib import admin

from .models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    DrefCountryDistrict,
    DrefImage,
)


@admin.register(PlannedIntervention)
class PlannedInterventionAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(IdentifiedNeed)
class IdentifiedNeedAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(NationalSocietyAction)
class NationalSocietyActiondAdmin(admin.ModelAdmin):
    list_display = ('title',)


class DrefCountryDistrictAdminInline(admin.TabularInline):
    model = DrefCountryDistrict
    extra = 0


class DrefImageAdminInline(admin.StackedInline):
    model = DrefImage


@admin.register(Dref)
class DrefAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'national_society', 'disaster_type',
                    'ns_request_date', 'submission_to_geneva', 'status')
    inlines = [DrefCountryDistrictAdminInline, DrefImageAdminInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'planned_interventions', 'needs_identified', 'national_society_actions')
