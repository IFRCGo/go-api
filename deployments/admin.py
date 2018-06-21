from django.contrib import admin
import deployments.models as models


class ERUInline(admin.TabularInline):
    model = models.ERU
    autocomplete_fields = ('deployed_to', 'event',)


class ERUOwnerAdmin(admin.ModelAdmin):
    inlines = [ERUInline]
    autocomplete_fields = ('national_society_country',)


class FactPersonInline(admin.TabularInline):
    model = models.FactPerson


class FactAdmin(admin.ModelAdmin):
    inlines = [FactPersonInline]


class RdrtPersonInline(admin.TabularInline):
    model = models.RdrtPerson


class RdrtAdmin(admin.ModelAdmin):
    inlines = [RdrtPersonInline]


class PartnerSocietyDeploymentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('parent_society', 'country_deployed_to', 'district_deployed_to',)


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop)
admin.site.register(models.Fact, FactAdmin)
admin.site.register(models.Rdrt, RdrtAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
admin.site.register(models.PartnerSocietyActivities)
