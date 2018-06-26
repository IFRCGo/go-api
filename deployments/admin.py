from django.contrib import admin
import deployments.models as models
from api.admin_classes import RegionRestrictedAdmin


class ERUInline(admin.TabularInline):
    model = models.ERU
    autocomplete_fields = ('deployed_to', 'event',)


class ERUOwnerAdmin(RegionRestrictedAdmin):
    country_in = 'national_society_country__in'
    region_in = 'national_society_country__region__in'
    inlines = [ERUInline]
    autocomplete_fields = ('national_society_country',)
    search_fields = ('national_society_country__name',)


class HeopAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'region__pk__in'
    search_fields = ('country__name', 'region__name', 'person', 'role',)


class FactPersonInline(admin.TabularInline):
    model = models.FactPerson


class FactAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'region__pk__in'
    inlines = [FactPersonInline]
    search_fields = ('country__name', 'region__name',)


class RdrtPersonInline(admin.TabularInline):
    model = models.RdrtPerson


class RdrtAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'region__pk__in'
    inlines = [RdrtPersonInline]
    search_fields = ('country__name', 'region__name',)


class PartnerSocietyActivityAdmin(admin.ModelAdmin):
    search_fields = ('activity',)


class PartnerSocietyDeploymentAdmin(RegionRestrictedAdmin):
    country_in = 'parent_society__in'
    region_in = 'parent_society__region__in'
    autocomplete_fields = ('parent_society', 'country_deployed_to', 'district_deployed_to',)
    search_fields = ('activity__activity', 'name', 'role', 'country_deployed_to__name', 'parent_society__name', 'district_deployed_to__name',)


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop, HeopAdmin)
admin.site.register(models.Fact, FactAdmin)
admin.site.register(models.Rdrt, RdrtAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
admin.site.register(models.PartnerSocietyActivities, PartnerSocietyActivityAdmin)
