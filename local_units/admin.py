from django.contrib.gis import admin
from admin_auto_filters.filters import AutocompleteFilterFactory

from .models import (
    LocalUnit,
    LocalUnitType,
    LocalUnitLevel,
    DelegationOffice,
    DelegationOfficeType,
)


@admin.register(LocalUnitType)
class LocalUnitTypeAdmin(admin.ModelAdmin):
    ordering=('code',)
    search_fields = ('name',)


@admin.register(LocalUnitLevel)
class LocalUnitLevel(admin.ModelAdmin):
    ordering=('level',)
    search_fields = ('name',)


@admin.register(LocalUnit)
class LocalUnitAdmin(admin.OSMGeoAdmin):
    search_fields = (
        'english_branch_name',
        'local_branch_name',
        'city_loc',
        'city_en',
        'country',
        'country__name'
    )
    autocomplete_fields = (
        'country',
        'type',
        'level'
    )
    list_filter = (
        AutocompleteFilterFactory('Country', 'country'),
    )




@admin.register(DelegationOffice)
class DelegationOfficeAdmin(admin.OSMGeoAdmin):
    search_fields = (
        'name',
        'city',
        'country',
        'country__name'
    )

    autocomplete_fields = (
        'country',
    )
    list_filter = (
        AutocompleteFilterFactory('Country', 'country'),
    )

@admin.register(DelegationOfficeType)
class DelegationOfficeTypeAdmin(admin.ModelAdmin):
    ordering=('code',)
