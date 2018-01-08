from django.contrib import admin
import deployments.models as models


class ERUInline(admin.TabularInline):
    model = models.ERU


class ERUOwnerAdmin(admin.ModelAdmin):
    inlines = [ERUInline]


admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.Heop)
