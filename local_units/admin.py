from django.contrib.gis import admin

from .models import LocalUnit, LocalUnitType

admin.site.register(LocalUnit, admin.OSMGeoAdmin, search_fields=(
    'english_branch_name',
    'local_branch_name',
    'city_loc',
    'city_en',
    'country__name'))
admin.site.register(LocalUnitType, admin.ModelAdmin, ordering=('level',))
