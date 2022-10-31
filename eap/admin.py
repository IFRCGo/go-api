from django.contrib import admin

# Register your models here.

from .models import (
    EAP,
    EAPPartner,
    EAPReference,
    EAPDocument,
    EAPActivation,
    EAPActivationReport,
)


class ReferenceAdminInline(admin.TabularInline):
    model = EAPReference
    extra = 0


class PartnerAdminInline(admin.TabularInline):
    model = EAPPartner
    extra = 0


@admin.register(EAPDocument)
class EAPDocumentAdmin(admin.ModelAdmin):
    model = EAPDocument
    extra = 0


@admin.register(EAP)
class EAPAdmin(admin.ModelAdmin):
    list_display = ('eap_number', 'country', 'status', 'operational_timeframe',)
    inlines = [ReferenceAdminInline, PartnerAdminInline]
    autocomplete_fields = ('country', 'districts', 'disaster_type', 'created_by', 'modified_by')


@admin.register(EAPActivation)
class EAPActivation(admin.ModelAdmin):
    model = EAPActivation


@admin.register(EAPActivationReport)
class EAPActivationReport(admin.ModelAdmin):
    model = EAPActivationReport
