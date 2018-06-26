from django.contrib import admin
import deployments.models as models


class ERUInline(admin.TabularInline):
    model = models.ERU
    autocomplete_fields = ('deployed_to', 'event',)


class ERUOwnerAdmin(admin.ModelAdmin):
    inlines = [ERUInline]
    autocomplete_fields = ('national_society_country',)
    search_fields = ('national_society_country__name',)


class HeopAdmin(admin.ModelAdmin):
    search_fields = ('country__name', 'region__name', 'person', 'role',)


class FactPersonInline(admin.TabularInline):
    model = models.FactPerson


class FactAdmin(admin.ModelAdmin):
    inlines = [FactPersonInline]
    search_fields = ('country__name', 'region__name',)


class RdrtPersonInline(admin.TabularInline):
    model = models.RdrtPerson


class RdrtAdmin(admin.ModelAdmin):
    inlines = [RdrtPersonInline]
    search_fields = ('country__name', 'region__name',)


class PartnerSocietyActivityAdmin(admin.ModelAdmin):
    search_fields = ('activity',)


class PartnerSocietyDeploymentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('parent_society', 'country_deployed_to', 'district_deployed_to',)
    search_fields = ('activity__activity', 'name', 'role', 'country_deployed_to__name', 'parent_society__name', 'district_deployed_to__name',)


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop, HeopAdmin)
admin.site.register(models.Fact, FactAdmin)
admin.site.register(models.Rdrt, RdrtAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
admin.site.register(models.PartnerSocietyActivities, PartnerSocietyActivityAdmin)
