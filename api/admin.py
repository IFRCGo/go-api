from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from api.event_sources import SOURCES
from api.admin_classes import RegionRestrictedAdmin
import api.models as models


class HasRelatedEventFilter(admin.SimpleListFilter):
    title = _('related emergency')
    parameter_name = 'related_emergency'
    def lookups(self, request, model_admin):
        return (
            ('yes', _('Exists')),
            ('confirm', _('Needs confirmation')),
            ('no', _('None')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(event__isnull=False).filter(needs_confirmation=False)
        if self.value() == 'confirm':
            return queryset.filter(event__isnull=False).filter(needs_confirmation=True)
        if self.value() == 'no':
            return queryset.filter(event__isnull=True)


class MembershipFilter(admin.SimpleListFilter):
    title = _('membership')
    parameter_name = 'membership'
    def lookups(self, request, model_admin):
        return (
            ('membership', _('Membership')),
            ('ifrc', _('IFRC')),
            ('public', _('Public')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'membership':
            return queryset.filter(atype=models.VisibilityChoices.MEMBERSHIP)
        if self.value() == 'ifrc':
            return queryset.filter(atype=models.VisibilityChoices.IFRC)
        if self.value() == 'public':
            return queryset.filter(atype=models.VisibilityChoices.PUBLIC)


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


class IsFeaturedFilter(admin.SimpleListFilter):
    title = _('featured')
    parameter_name = 'featured'
    def lookups(self, request, model_admin):
        return (
            ('featured', _('Featured')),
            ('not', _('Not Featured')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'featured':
            return queryset.filter(is_featured=True)
        if self.value() == 'not':
            return queryset.filter(is_featured=False)


class EventSourceFilter(admin.SimpleListFilter):
    title = _('source')
    parameter_name = 'event_source'
    def lookups(self, request, model_admin):
        return (
            ('input', _('Manual input')),
            ('gdacs', _('GDACs scraper')),
            ('report_ingest', _('Field report ingest')),
            ('report_admin', _('Field report admin')),
            ('appeal_admin', _('Appeals admin')),
            ('unknown', _('Unknown automated')),
        )
    def queryset(self, request, queryset):
        if self.value() == 'input':
            return queryset.filter(auto_generated=False)
        if self.value() == 'gdacs':
            return queryset.filter(auto_generated_source=SOURCES['gdacs'])
        if self.value() == 'report_ingest':
            return queryset.filter(auto_generated_source=SOURCES['report_ingest'])
        if self.value() == 'report_admin':
            return queryset.filter(auto_generated_source=SOURCES['report_admin'])
        if self.value() == 'appeal_admin':
            return queryset.filter(auto_generated_source=SOURCES['appeal_admin'])
        if self.value() == 'unknown':
            return queryset.filter(auto_generated=True).filter(auto_generated_source__isnull=True)


class DisasterTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class KeyFigureInline(admin.TabularInline):
    model = models.KeyFigure


class SnippetInline(admin.TabularInline):
    model = models.Snippet


class EventContactInline(admin.TabularInline):
    model = models.EventContact


class SituationReportInline(admin.TabularInline):
    model = models.SituationReport


class EventAdmin(RegionRestrictedAdmin):
    country_in = 'countries__pk__in'
    region_in = 'regions__pk__in'

    inlines = [KeyFigureInline, SnippetInline, EventContactInline, SituationReportInline]
    list_display = ('name', 'alert_level', 'glide', 'auto_generated', 'auto_generated_source',)
    list_filter = [IsFeaturedFilter, EventSourceFilter,]
    search_fields = ('name', 'countries__name', 'dtype__name',)
    readonly_fields = ('appeals', 'field_reports', 'auto_generated_source',)
    autocomplete_fields = ('countries', 'districts',)
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


class GdacsAdmin(RegionRestrictedAdmin):
    country_in = 'countries__pk__in'
    region_in = None
    search_fields = ('title',)


class ActionsTakenInline(admin.TabularInline):
    model = models.ActionsTaken


class SourceInline(admin.TabularInline):
    model = models.Source


class FieldReportContactInline(admin.TabularInline):
    model = models.FieldReportContact


class FieldReportAdmin(RegionRestrictedAdmin):
    country_in = 'countries__pk__in'
    region_in = 'regions__pk__in'

    inlines = [ActionsTakenInline, SourceInline, FieldReportContactInline]
    list_display = ('summary', 'event', 'visibility',)
    list_select_related = ('event',)
    search_fields = ('countries', 'regions', 'summary',)
    autocomplete_fields = ('event', 'countries', 'districts',)
    readonly_fields = ('report_date', 'created_at', 'updated_at',)
    list_filter = [HasRelatedEventFilter, MembershipFilter,]
    actions = ['create_events',]

    def create_events(self, request, queryset):
        for report in queryset:
            event = models.Event.objects.create(
                name=report.summary,
                dtype=getattr(report, 'dtype'),
                disaster_start_date=getattr(report, 'created_at'),
                auto_generated=True,
                auto_generated_source=SOURCES['report_admin'],
            )
            if getattr(report, 'countries').exists():
                for country in report.countries.all():
                    event.countries.add(country)
            if getattr(report, 'regions').exists():
                for region in report.regions.all():
                    event.regions.add(region)
            report.event = event
            report.save()
        self.message_user(request, '%s emergency object(s) created' % queryset.count())
    create_events.short_description = 'Create emergencies from selected reports'


class AppealDocumentInline(admin.TabularInline):
    model = models.AppealDocument


class AppealAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'region__pk__in'
    inlines = [AppealDocumentInline]
    list_display = ('code', 'name', 'atype', 'needs_confirmation', 'event', 'start_date',)
    list_select_related = ('event',)
    search_fields = ('code', 'name',)
    readonly_fields = ('region',)
    list_filter = [HasRelatedEventFilter, AppealTypeFilter,]
    actions = ['create_events', 'confirm_events',]
    autocomplete_fields = ('event', 'country',)

    def create_events(self, request, queryset):
        for appeal in queryset:
            event = models.Event.objects.create(
                name=appeal.name,
                dtype=getattr(appeal, 'dtype'),
                disaster_start_date=getattr(appeal, 'start_date'),
                auto_generated=True,
                auto_generated_source=SOURCES['appeal_admin'],
            )
            if appeal.country is not None:
                event.countries.add(appeal.country)
            if appeal.region is not None:
                event.regions.add(appeal.region)
            appeal.event = event
            appeal.save()
        self.message_user(request, '%s emergency object(s) created' % queryset.count())
    create_events.short_description = 'Create emergencies from selected appeals'

    def confirm_events(self, request, queryset):
        errors = []
        for appeal in queryset:
            if not appeal.needs_confirmation or not appeal.event:
                errors.append(appeal.code)
        if len(errors):
            self.message_user(request, '%s %s not have an unconfirmed event.' % (', '.join(errors), 'does' if len(errors) == 1 else 'do'),
                              level=messages.ERROR)
        else:
            for appeal in queryset:
                appeal.needs_confirmation = False
                appeal.save()
    confirm_events.short_description = 'Confirm emergencies as correct'

    def save_model(self, request, obj, form, change):
        if (obj.country):
            obj.region = obj.country.region
        super().save_model(request, obj, form, change)


class AppealDocumentAdmin(RegionRestrictedAdmin):
    country_in = 'appeal__country__in'
    region_in = 'appeal__region__in'
    search_fields = ('name', 'appeal__code', 'appeal__name')


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


class DistrictAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'country__region__in'
    search_fields = ('name', 'country_name',)


class CountryAdmin(RegionRestrictedAdmin):
    country_in = 'pk__in'
    region_in = 'region__pk__in'
    search_fields = ('name',)
    inlines = [CountryKeyFigureInline, CountrySnippetInline, CountryLinkInline, CountryContactInline,]


class RegionAdmin(RegionRestrictedAdmin):
    country_in = None
    region_in = 'pk__in'
    inlines = [RegionKeyFigureInline, RegionSnippetInline, RegionLinkInline, RegionContactInline,]
    search_fields = ('name',)


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email',)


class SituationReportAdmin(RegionRestrictedAdmin):
    country_in = 'event__countries__in'
    region_in = 'event__regions__in'
    search_fields = ('name', 'event__name',)


admin.site.register(models.DisasterType, DisasterTypeAdmin)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.GDACSEvent, GdacsAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.District, DistrictAdmin)
admin.site.register(models.Appeal, AppealAdmin)
admin.site.register(models.AppealDocument, AppealDocumentAdmin)
admin.site.register(models.FieldReport, FieldReportAdmin)
admin.site.register(models.Profile, UserProfileAdmin)
admin.site.register(models.SituationReport, SituationReportAdmin)
