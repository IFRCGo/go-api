from django.contrib import admin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    DrefCountryDistrict,
    DrefFile,
    DrefOperationalUpdate,
    DrefOperationalUpdateCountryDistrict,
    DrefFinalReport,
    DrefFinalReportCountryDistrict,
)


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ('file',)


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


class DrefOperationalUpdateCountryDistrictAdminInline(admin.TabularInline):
    model = DrefOperationalUpdateCountryDistrict
    extra = 0
    autocomplete_fields = ('country', 'district',)


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'images',
    )
    inlines = [DrefOperationalUpdateCountryDistrictAdminInline]
    list_filter = ['dref']


class DrefFinalReportCountryDistrictAdminInline(admin.TabularInline):
    model = DrefFinalReportCountryDistrict
    extra = 0
    autocomplete_fields = ('country', 'district',)


@admin.register(DrefFinalReport)
class DrefFinalReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'photos',
    )
    inlines = [DrefFinalReportCountryDistrictAdminInline]
    list_filter = ['dref']
    search_fields = ['title', 'national_society__name']
