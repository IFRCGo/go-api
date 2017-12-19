from django.contrib import admin
import api.models as models


class KeyFigureInline(admin.TabularInline):
    model = models.KeyFigure


class SnippetInline(admin.TabularInline):
    model = models.Snippet


class EventAdmin(admin.ModelAdmin):
    inlines = [KeyFigureInline, SnippetInline]


class ActionsTakenInline(admin.TabularInline):
    model = models.ActionsTaken


class SourceInline(admin.TabularInline):
    model = models.Source


class FieldReportAdmin(admin.ModelAdmin):
    inlines = [ActionsTakenInline, SourceInline]


class ERUInline(admin.TabularInline):
    model = models.ERU


class ERUOwnerAdmin(admin.ModelAdmin):
    inlines = [ERUInline]


admin.site.register(models.DisasterType)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.GDACSEvent)
admin.site.register(models.Country)
admin.site.register(models.Appeal)
admin.site.register(models.FieldReport, FieldReportAdmin)
admin.site.register(models.SourceType)
admin.site.register(models.Source)
admin.site.register(models.Contact)
admin.site.register(models.ERUOwner, ERUOwnerAdmin)
