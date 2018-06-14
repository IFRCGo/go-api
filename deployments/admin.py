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


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop)
admin.site.register(models.Fact, FactAdmin)
admin.site.register(models.Rdrt, RdrtAdmin)
admin.site.register(models.PartnerSocietyDeployment)
