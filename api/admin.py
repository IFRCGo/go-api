from django.contrib import admin
import api.models as models


class ERUInline(admin.TabularInline):
    model = models.ERU


class DeploymentAdmin(admin.ModelAdmin):
    inlines = [ERUInline]


# Register your models here.
admin.site.register(models.DisasterType)
admin.site.register(models.Event)
admin.site.register(models.GDACSEvent)
admin.site.register(models.Country)
admin.site.register(models.Appeal)
admin.site.register(models.FieldReport)
admin.site.register(models.ActionsTaken)
admin.site.register(models.SourceType)
admin.site.register(models.Source)
admin.site.register(models.Contact)
admin.site.register(models.Deployment, DeploymentAdmin)
