from django.contrib import admin

from .models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalReferences,
    InformalAction,
    InformalCountryDistrict
)


@admin.register(InformalGraphicMap)
class InformalGraphicMapAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalReferences)
class InformalReferencesAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalAction)
class InformalActionAdmin(admin.ModelAdmin):
    pass


class InformalCountryDistrictAdminInline(admin.TabularInline):
    model = InformalCountryDistrict
    extra = 0


@admin.register(InformalUpdate)
class InformalUpdateAdmin(admin.ModelAdmin):
    inlines = [InformalCountryDistrictAdminInline]
