from django.contrib import admin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
    DrefFinalReportCountryDistrict,
    DrefFileUpload
)


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ('file',)


@admin.register(Dref)
class DrefAdmin(TranslationAdmin, admin.ModelAdmin):
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
class DrefOperationalUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'images',
    )
    list_filter = ['dref']


@admin.register(DrefFinalReport)
class DrefFinalReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'national_society', 'disaster_type')
    autocomplete_fields = (
        'national_society',
        'disaster_type',
        'photos',
    )
    list_filter = ['dref']
    search_fields = ['title', 'national_society__name']
@admin.register(DrefFileUpload)
class DrefFileUploadAdmin(admin.ModelAdmin):
    pass
