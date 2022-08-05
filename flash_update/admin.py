from django.contrib import admin

from lang.admin import TranslationAdmin

from .models import (
    FlashUpdate,
    FlashGraphicMap,
    FlashReferences,
    FlashAction,
    FlashActionsTaken,
    FlashCountryDistrict,
    FlashEmailSubscriptions,
    Donors,
    DonorGroup,
    FlashUpdateShare,
)

from .forms import ActionForm


class FlashActionAdmin(admin.ModelAdmin):
    form = ActionForm
    list_display = ('__str__', 'organizations', 'category',)


@admin.register(FlashGraphicMap)
class FlashGraphicMapAdmin(admin.ModelAdmin):
    pass


@admin.register(FlashReferences)
class FlashReferencesAdmin(admin.ModelAdmin):
    pass


@admin.register(FlashEmailSubscriptions)
class FlashEmailSubscriptionsAdmin(admin.ModelAdmin):
    autocomplete_fields = ('group',)

    def has_add_permission(self, request, obj=None):
        return False


class FlashActionTakenAdminInline(admin.TabularInline):
    model = FlashActionsTaken
    extra = 0


@admin.register(DonorGroup)
class DonorGroup(admin.ModelAdmin):
    pass


@admin.register(Donors)
class DonorsAdmin(admin.ModelAdmin):
    pass


@admin.register(FlashUpdateShare)
class ShareFlashUpdateAdmin(admin.ModelAdmin):
    pass


class FlashCountryDistrictAdminInline(admin.TabularInline):
    model = FlashCountryDistrict
    extra = 0
    autocomplete_fields = ('country', 'district',)


@admin.register(FlashUpdate)
class FlashUpdateAdmin(TranslationAdmin):
    inlines = [FlashCountryDistrictAdminInline, FlashActionTakenAdminInline]
    search_fields = ('title',)
    list_filter = ('hazard_type', 'share_with', 'flash_country_district__country')


admin.site.register(FlashAction, FlashActionAdmin)
