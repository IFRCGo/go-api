from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
import api.models as models


class HasRelatedEventFilter(admin.SimpleListFilter):
    title = _('related emergency')
    parameter_name = 'related_emergency'
    def lookups(self, request, model_admin):
        return (
            ('yes', _('Exists')),
            ('no', _('None')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(event__isnull=False)
        if self.value() == 'no':
            return queryset.filter(event__isnull=True)


class AppealTypeFilter(admin.SimpleListFilter):
    title = _('appeal type')
    parameter_name = 'appeal_type'
    def lookups(self, request, model_admin):
        return (
            ('dref', _('DREF')),
            ('appeal', _('Appeal')),
            ('intl', _('Intl appeal')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'dref':
            return queryset.filter(atype=models.AppealType.DREF)
        if self.value() == 'appeal':
            return queryset.filter(atype=models.AppealType.APPEAL)
        if self.value() == 'intl':
            return queryset.filter(atype=models.AppealType.INTL)


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
    readonly_fields = ('appeals', 'field_reports', )
    def appeals(self, instance):
        if getattr(instance, 'appeals').exists():
            return format_html_join(
                mark_safe('<br />'),
                '{} - {}',
                ((appeal.code, appeal.name) for appeal in instance.appeals.all())
            )
        return mark_safe('<span class="errors">No related appeals</span>')
    appeals.short_description = 'Appeals'

    def field_reports(self, instance):
        if getattr(instance, 'field_reports').exists():
            return format_html_join(
                mark_safe('<br />'),
                '{} - {}',
                ((report.pk, report.summary) for report in instance.field_reports.all())
            )
        return mark_safe('<span class="errors">No related field reports</span>')
    field_reports.short_description = 'Field Reports'


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
    list_display = ('code', 'name', 'atype', 'event', 'start_date', 'end_date',)
    list_editable = ('event',)
    list_select_related = ('event',)
    search_fields = ['code', 'name',]
    readonly_fields = ('region',)
    list_filter = [HasRelatedEventFilter, AppealTypeFilter,]
    actions = ['create_events',]

    def create_events(self, request, queryset):
        for appeal in queryset:
            event = models.Event.objects.create(
                name=appeal.name,
                dtype=getattr(appeal, 'dtype'),
                disaster_start_date=getattr(appeal, 'start_date'),
                auto_generated=True,
            )
            if appeal.country is not None:
                event.countries.add(appeal.country)
            if appeal.region is not None:
                event.regions.add(appeal.region)
            appeal.event = event
            appeal.save()
        self.message_user(request, '%s emergency object(s) created' % queryset.count())
    create_events.short_description = 'Create emergencies from selected appeals'

    def save_model(self, request, obj, form, change):
        if (obj.country):
            obj.region = obj.country.region
        super().save_model(request, obj, form, change)


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
