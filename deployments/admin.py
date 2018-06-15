from django.contrib import admin
import deployments.models as models


class ERUInline(admin.TabularInline):
    model = models.ERU


class ERUOwnerAdmin(admin.ModelAdmin):
    inlines = [ERUInline]


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
    readonly_fields = ('country_deployed_to',)
    def save_model(self, request, obj, form, change):
        if (obj.district_deployed_to):
            obj.country_deployed_to = obj.district_deployed_to.country
        super().save_model(request, obj, form, change)


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop)
admin.site.register(models.Fact, FactAdmin)
admin.site.register(models.Rdrt, RdrtAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
