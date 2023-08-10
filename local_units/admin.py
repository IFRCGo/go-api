from django.contrib.gis import admin

from .models import LocalUnit, LocalUnitType

admin.site.register(LocalUnit, admin.OSMGeoAdmin)
admin.site.register(LocalUnitType, admin.ModelAdmin, ordering=('level',))
