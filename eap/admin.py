from django.contrib import admin

# Register your models here.
from .models import EAP


@admin.register(EAP)
class EAPAdmin(admin.ModelAdmin):
    list_display = ('eap_number', 'country', 'status', 'operational_timeframe', 'total_budget')

