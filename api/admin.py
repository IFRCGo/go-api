from django.contrib import admin
from .models import DisasterType, Event, GDACSEvent, Country, FieldReport, Appeal, ActionsTaken, SourceType, Source

# Register your models here.
admin.site.register(DisasterType)
admin.site.register(Event)
admin.site.register(GDACSEvent)
admin.site.register(Country)
admin.site.register(Appeal)
admin.site.register(FieldReport)
admin.site.register(ActionsTaken)
admin.site.register(SourceType)
admin.site.register(Source)
