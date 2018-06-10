from django.contrib import admin
import api.models as models


class KeyFigureInline(admin.TabularInline):
    model = models.KeyFigure


class SnippetInline(admin.TabularInline):
    model = models.Snippet


class EventContactInline(admin.TabularInline):
    model = models.EventContact


class SituationReportInline(admin.TabularInline):
    model = models.SituationReport


class EventAdmin(admin.ModelAdmin):
    inlines = [KeyFigureInline, SnippetInline, EventContactInline, SituationReportInline]


class ActionsTakenInline(admin.TabularInline):
    model = models.ActionsTaken


class SourceInline(admin.TabularInline):
    model = models.Source


class FieldReportContactInline(admin.TabularInline):
    model = models.FieldReportContact


class FieldReportAdmin(admin.ModelAdmin):
    inlines = [ActionsTakenInline, SourceInline, FieldReportContactInline]


class AppealDocumentInline(admin.TabularInline):
    model = models.AppealDocument


class AppealAdmin(admin.ModelAdmin):
    inlines = [AppealDocumentInline]
    list_display = ('code', 'name', 'start_date')


class CountryKeyFigureInline(admin.TabularInline):
    model = models.CountryKeyFigure


class RegionKeyFigureInline(admin.TabularInline):
    model = models.RegionKeyFigure


class CountrySnippetInline(admin.TabularInline):
    model = models.CountrySnippet


class RegionSnippetInline(admin.TabularInline):
    model = models.RegionSnippet


class CountryLinkInline(admin.TabularInline):
    model = models.CountryLink


class RegionLinkInline(admin.TabularInline):
    model = models.RegionLink


class CountryContactInline(admin.TabularInline):
    model = models.CountryContact


class RegionContactInline(admin.TabularInline):
    model = models.RegionContact


class CountryAdmin(admin.ModelAdmin):
    inlines = [CountryKeyFigureInline, CountrySnippetInline, CountryLinkInline, CountryContactInline,]


class RegionAdmin(admin.ModelAdmin):
    inlines = [RegionKeyFigureInline, RegionSnippetInline, RegionLinkInline, RegionContactInline,]


admin.site.register(models.DisasterType)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.GDACSEvent)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.Appeal, AppealAdmin)
admin.site.register(models.AppealDocument)
admin.site.register(models.FieldReport, FieldReportAdmin)
admin.site.register(models.Profile)
admin.site.register(models.SituationReport)
