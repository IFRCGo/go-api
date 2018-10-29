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


class PersonnelAdmin(admin.ModelAdmin):
    country_in = 'country_from__in'
    region_in = 'country_from__region__in'
    search_fields = ('name', 'role', 'type',)
    list_display = ('name', 'role', 'start_date', 'end_date', 'country_from', 'deployment',)


class PersonnelInline(admin.TabularInline):
    model = models.Personnel


class PersonnelDeploymentAdmin(admin.ModelAdmin):
    search_fields = ('country_deployed_to', 'region_deployed_to',)
    autocomplete_fields = ('event_deployed_to',)
    inlines = [PersonnelInline]
    list_display = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to', 'comments',)


class PartnerSocietyActivityAdmin(admin.ModelAdmin):
    search_fields = ('activity',)


class PartnerSocietyDeploymentAdmin(RegionRestrictedAdmin):
    country_in = 'parent_society__in'
    region_in = 'parent_society__region__in'
    autocomplete_fields = ('parent_society', 'country_deployed_to', 'district_deployed_to',)
    search_fields = ('activity__activity', 'name', 'role', 'country_deployed_to__name', 'parent_society__name', 'district_deployed_to__name',)
    list_display = ('name', 'role', 'activity', 'parent_society', 'country_deployed_to', 'start_date', 'end_date',)


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.PersonnelDeployment, PersonnelDeploymentAdmin)
admin.site.register(models.Personnel, PersonnelAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
admin.site.register(models.PartnerSocietyActivities, PartnerSocietyActivityAdmin)
