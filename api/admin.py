import os
import csv
import time
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from api.event_sources import SOURCES
from api.admin_classes import RegionRestrictedAdmin
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, ChoiceDropdownFilter, RelatedDropdownFilter
)
import api.models as models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token
from django.http import HttpResponse
from .forms import ActionForm

class GoUserAdmin(UserAdmin):
    list_filter = (
        ('profile__country__region', RelatedDropdownFilter),
        ('profile__country', RelatedDropdownFilter),
        ('groups', RelatedDropdownFilter),
        'is_staff',
        'is_superuser',
        'is_active',
    )

admin.site.unregister(User)
admin.site.register(User, GoUserAdmin)

class GoTokenAdmin(TokenAdmin):
    search_fields = ('user__username', 'user__email',)

admin.site.unregister(Token)
admin.site.register(Token, GoTokenAdmin)


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
            return queryset.filter(visibility=models.VisibilityChoices.MEMBERSHIP)
        if self.value() == 'ifrc':
            return queryset.filter(visibility=models.VisibilityChoices.IFRC)
        if self.value() == 'public':
            return queryset.filter(visibility=models.VisibilityChoices.PUBLIC)


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
            ('who', _('WHO scraper')),
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
        if self.value() == 'who':
            return queryset.filter(auto_generated_source__startswith='www.who.int')
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
    list_display = ('name', 'ifrc_severity_level', 'glide', 'auto_generated', 'auto_generated_source',)
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

# For multiple document fields inline. TO be FIXED: only the last one is saved. Change also tabular.html (DELETEME)
#   def save_formset(self, request, form, formset, change):
#       if hasattr(formset.model, 'document'): # SituationReports (or other similars)
#           instances = formset.save(commit=False)
#           for inst in formset.deleted_objects:
#               inst.delete()
#           for inst in formset.changed_objects:
#               inst.save()
#           for inst in formset.new_objects:
#               for i,one_document in enumerate(request.FILES.getlist('documents_multiple')):
#                   if i<30: # not letting tons of documents to be attached
#                       inst.name     = inst.name if i == 0 else inst.name + '-' + str(i)
#                       inst.document = one_document
#                       inst.save()
#           formset.save_m2m()
#       else:
#           formset.save()


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
    search_fields = ('countries__name', 'regions__name', 'summary',)
    autocomplete_fields = ('event', 'countries', 'districts',)
    readonly_fields = ('report_date', 'created_at', 'updated_at',)
    list_filter = [MembershipFilter,]
    actions = ['create_events', 'export_field_reports', ]

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

    def export_field_reports(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        timestr = time.strftime("%Y%m%d-%H%M%S")

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=FieldReports_export_{}.csv'.format(
            timestr)
        writer = csv.writer(response)

        writer.writerow(field_names)

        for fr in queryset:
            row = writer.writerow([getattr(fr, field) for field in field_names])
        return response
    export_field_reports.short_description = 'Export selected Field Reports to CSV'

    def get_actions(self, request):
        actions = super(FieldReportAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['export_field_reports']
        return actions

class ActionAdmin(admin.ModelAdmin):
    form = ActionForm
    list_display = ('__str__', 'field_report_types', 'organizations',)


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
    list_display = ('__str__', 'record_type')
    region_in = 'region__pk__in'
    list_editable = ('record_type',)
    search_fields = ('name',)
    inlines = [CountryKeyFigureInline, CountrySnippetInline, CountryLinkInline, CountryContactInline,]
    exclude = ('key_priorities',)


class RegionAdmin(RegionRestrictedAdmin):
    country_in = None
    region_in = 'pk__in'
    inlines = [RegionKeyFigureInline, RegionSnippetInline, RegionLinkInline, RegionContactInline,]
    search_fields = ('name',)


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email', 'country__name',)
    list_filter = (
        ('country__region', RelatedDropdownFilter),
        ('country', RelatedDropdownFilter),
    )
    actions = ['export_selected_users',]

    def export_selected_users(self, request, queryset):
        meta = self.model._meta
        prof_field_names = [field.name for field in meta.fields]
        user_field_names = [field.name for field in models.User._meta.fields if field.name!="password"]
        timestr = time.strftime("%Y%m%d-%H%M%S")

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Users_export_{}.csv'.format(
            timestr)
        writer = csv.writer(response)

        writer.writerow(prof_field_names + user_field_names + ['groups'])

        for prof in queryset:

            user_model = models.User.objects.get(id=prof.user_id)
            user_groups = list(user_model.groups.values_list('name',flat = True))
            user_groups_string = ', '.join(user_groups) if user_groups else ''

            row = writer.writerow([getattr(prof, field) for field in prof_field_names] + [
                                  getattr(user_model, field) for field in user_field_names] + [user_groups_string] )
        return response
    export_selected_users.short_description = 'Export selected Users with their Profiles'

    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['export_selected_users']
        return actions


class SituationReportAdmin(RegionRestrictedAdmin):
    country_in = 'event__countries__in'
    region_in = 'event__regions__in'
    autocomplete_fields = ('event',)

# Works, but gives azure storageclient ERROR - Client-Request-ID=... Retry policy did not allow for a retry: ... HTTP status code=404, Exception=The specified blob does not exist.
# Has a duplication at PER NiceDocuments
    def save_model(self, request, obj, form, change):
       if change:
           obj.save()
       else:
           for i,one_document in enumerate(request.FILES.getlist('documents_multiple')):
               if i<30: # not letting tons of documents to be attached
                   models.SituationReport.objects.create(
                       name        =obj.name if i == 0 else obj.name + '-' + str(i),
                       document    =one_document,
                       document_url=obj.document_url,
                       event       =obj.event,
                       type        =obj.type,
                       visibility  =obj.visibility,
                       )

class SituationReportTypeAdmin(admin.ModelAdmin):
    search_fields = ('type',)


class EmergencyOperationsDatasetAdmin(admin.ModelAdmin):
    search_fields = ('file_name', 'raw_file_name', 'appeal_number',)
    list_display = ('file_name', 'raw_file_name', 'raw_file_url', 'appeal_number', 'is_validated',)
    readonly_fields = (
        'raw_file_name',
        'raw_file_url',
        'raw_appeal_launch_date',
        'raw_appeal_number',
        'raw_category_allocated',
        'raw_date_of_issue',
        'raw_dref_allocated',
        'raw_expected_end_date',
        'raw_expected_time_frame',
        'raw_glide_number',
        'raw_num_of_people_affected',
        'raw_num_of_people_to_be_assisted',
        'raw_disaster_risk_reduction_female',
        'raw_disaster_risk_reduction_male',
        'raw_disaster_risk_reduction_people_reached',
        'raw_disaster_risk_reduction_people_targeted',
        'raw_disaster_risk_reduction_requirements',
        'raw_health_female',
        'raw_health_male',
        'raw_health_people_reached',
        'raw_health_people_targeted',
        'raw_health_requirements',
        'raw_livelihoods_and_basic_needs_female',
        'raw_livelihoods_and_basic_needs_male',
        'raw_livelihoods_and_basic_needs_people_reached',
        'raw_livelihoods_and_basic_needs_people_targeted',
        'raw_livelihoods_and_basic_needs_requirements',
        'raw_migration_female',
        'raw_migration_male',
        'raw_migration_people_reached',
        'raw_migration_people_targeted',
        'raw_migration_requirements',
        'raw_protection_gender_and_inclusion_female',
        'raw_protection_gender_and_inclusion_male',
        'raw_protection_gender_and_inclusion_people_reached',
        'raw_protection_gender_and_inclusion_people_targeted',
        'raw_protection_gender_and_inclusion_requirements',
        'raw_shelter_female',
        'raw_shelter_male',
        'raw_shelter_people_reached',
        'raw_shelter_people_targeted',
        'raw_shelter_requirements',
        'raw_water_sanitation_and_hygiene_female',
        'raw_water_sanitation_and_hygiene_male',
        'raw_water_sanitation_and_hygiene_people_reached',
        'raw_water_sanitation_and_hygiene_people_targeted',
        'raw_water_sanitation_and_hygiene_requirements',
        'raw_education_female',
        'raw_education_male',
        'raw_education_people_reached',
        'raw_education_people_targeted',
        'raw_education_requirements',
    )


admin.site.register(models.DisasterType, DisasterTypeAdmin)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.GDACSEvent, GdacsAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.District, DistrictAdmin)
admin.site.register(models.Appeal, AppealAdmin)
admin.site.register(models.AppealDocument, AppealDocumentAdmin)
admin.site.register(models.FieldReport, FieldReportAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Profile, UserProfileAdmin)
admin.site.register(models.SituationReport, SituationReportAdmin)
admin.site.register(models.SituationReportType, SituationReportTypeAdmin)
admin.site.register(models.EmergencyOperationsDataset, EmergencyOperationsDatasetAdmin)
admin.site.site_url = 'https://' + os.environ.get('FRONTEND_URL')
admin.widgets.RelatedFieldWidgetWrapper.template_name = 'related_widget_wrapper.html'
