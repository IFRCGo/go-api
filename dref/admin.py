from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
)


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ('file',)


@admin.register(Dref)
class DrefAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'national_society', 'disaster_type',
                    'ns_request_date', 'submission_to_geneva', 'status',)
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


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'images',
        'users',
        'event_map',
        'images',
        'budget_file',
        'cover_image',
    )
    list_filter = ['dref']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'planned_interventions',
            'needs_identified',
            'national_society_actions',
            'users'
        )

@admin.register(DrefFinalReport)
class DrefFinalReportAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'photos',
    )
    list_filter = ['dref']
    search_fields = ['title', 'national_society__name']
