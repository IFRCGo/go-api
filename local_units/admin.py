from django.contrib.gis import admin

from .models import LocalUnit

admin.site.register(LocalUnit, admin.OSMGeoAdmin)
