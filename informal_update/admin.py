from django.contrib import admin

from .models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalReferences,
    InformalAction,
    InformalActionsTaken,
    InformalCountryDistrict,
    ReferenceUrls
)


@admin.register(ReferenceUrls)
class ReferenceUrlsAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalGraphicMap)
class InformalGraphicMapAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalReferences)
class InformalReferencesAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalAction)
class InformalActionAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalActionsTaken)
class InformalActionTakenAdmin(admin.ModelAdmin):
    pass


class InformalCountryDistrictAdminInline(admin.TabularInline):
    model = InformalCountryDistrict
    extra = 0
    autocomplete_fields = ('country', 'district',)


@admin.register(InformalUpdate)
class InformalUpdateAdmin(admin.ModelAdmin):
    inlines = [InformalCountryDistrictAdminInline]
    search_fields = ('title',)
    list_filter = ('hazard_type', 'share_with', 'informalcountrydistrict__country',)

