from django.contrib.gis import admin

from .models import LocalUnit, LocalUnitType, LocalUnitLevel, DelegationOffice, DelegationOfficeType

admin.site.register(LocalUnit, admin.OSMGeoAdmin, search_fields=(
    'english_branch_name',
    'local_branch_name',
    'city_loc',
    'city_en',
    'country__name'))
admin.site.register(LocalUnitType, admin.ModelAdmin, ordering=('code',))
admin.site.register(LocalUnitLevel, admin.ModelAdmin, ordering=('level',))
admin.site.register(DelegationOffice, admin.OSMGeoAdmin, search_fields=(
    'name',
    'city',
    'country__name'))
admin.site.register(DelegationOfficeType, admin.ModelAdmin, ordering=('code',))
