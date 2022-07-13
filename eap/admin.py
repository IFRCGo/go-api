from django.contrib import admin

# Register your models here.
from .models import EAP


@admin.register(EAP)
class EAPAdmin(admin.ModelAdmin):
    pass
