from django.contrib import admin
from .models import DisasterType, Event, Country, FieldReport

# Register your models here.
admin.site.register(DisasterType)
admin.site.register(Event)
admin.site.register(Country)
admin.site.register(FieldReport)
