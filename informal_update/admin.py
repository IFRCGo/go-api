from django.contrib import admin

from lang.admin import TranslationAdmin

from .models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalReferences,
    InformalAction,
    InformalActionsTaken,
    InformalCountryDistrict,
    InformalEmailSubscriptions,
    Donors
)

from .forms import ActionForm


class InformalActionAdmin(admin.ModelAdmin):
    form = ActionForm
    list_display = ('__str__', 'informal_update_types', 'organizations', 'category',)


@admin.register(InformalGraphicMap)
class InformalGraphicMapAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalReferences)
class InformalReferencesAdmin(admin.ModelAdmin):
    pass


@admin.register(InformalEmailSubscriptions)
class InformalEmailSubscriptionsAdmin(admin.ModelAdmin):
    autocomplete_fields = ('group',)

    def has_add_permission(self, request, obj=None):
        return False


class InformalActionTakenAdminInline(admin.TabularInline):
    model = InformalActionsTaken
    extra = 0


@admin.register(Donors)
class DonorsAdmin(admin.ModelAdmin):
    pass


class InformalCountryDistrictAdminInline(admin.TabularInline):
    model = InformalCountryDistrict
    extra = 0
    autocomplete_fields = ('country', 'district',)


@admin.register(InformalUpdate)
class InformalUpdateAdmin(TranslationAdmin):
    inlines = [InformalCountryDistrictAdminInline, InformalActionTakenAdminInline]
    search_fields = ('title',)
    list_filter = ('hazard_type', 'share_with', 'informalcountrydistrict__country',)


admin.site.register(InformalAction, InformalActionAdmin)
