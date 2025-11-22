import csv
import time

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, User
from django.contrib.gis import admin as geoadmin
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy
from reversion_compare.admin import CompareVersionAdmin

import api.models as models
from api.admin_classes import RegionRestrictedAdmin
from api.event_sources import SOURCES
from api.management.commands.index_and_notify import Command as Notify
from lang.admin import TranslationAdmin, TranslationInlineModelAdmin
from notifications.models import RecordType, SubscriptionType

from .forms import ActionForm, AppealForm

# from reversion.models import Revision


class ProfileInline(admin.StackedInline):
    model = models.Profile
    can_delete = False
    verbose_name_plural = _("user profile")
    fk_name = "user"
    readonly_fields = ("last_frontend_login",)


class GoUserAdmin(UserAdmin):

    @admin.display(description=_("name"))
    def name(self, obj):
        return obj.first_name + " " + obj.last_name

    inlines = (ProfileInline,)
    list_filter = (
        ("profile__country__region", RelatedDropdownFilter),
        ("profile__country", RelatedDropdownFilter),
        ("groups", RelatedDropdownFilter),
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_display = ("username", "email", "name", "is_active", "is_staff")

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, GoUserAdmin)


class GoTokenAdmin(TokenAdmin):
    search_fields = (
        "user__username",
        "user__email",
    )


admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, GoTokenAdmin)


class HasRelatedEventFilter(admin.SimpleListFilter):
    title = _("related emergency")
    parameter_name = "related_emergency"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Exists")),
            ("confirm", _("Needs confirmation")),
            ("no", _("None")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(event__isnull=False).filter(needs_confirmation=False)
        if self.value() == "confirm":
            return queryset.filter(event__isnull=False).filter(needs_confirmation=True)
        if self.value() == "no":
            return queryset.filter(event__isnull=True)


class MembershipFilter(admin.SimpleListFilter):
    title = _("membership")
    parameter_name = "membership"

    def lookups(self, request, model_admin):
        return models.VisibilityChoices.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(visibility=self.value())


class AppealTypeFilter(admin.SimpleListFilter):
    title = _("appeal type")
    parameter_name = "appeal_type"

    def lookups(self, request, model_admin):
        return models.AppealType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(atype=self.value())


class IsFeaturedFilter(admin.SimpleListFilter):
    title = _("featured")
    parameter_name = "featured"

    def lookups(self, request, model_admin):
        return (
            ("featured", _("Featured")),
            ("not", _("Not Featured")),
        )

    def queryset(self, request, queryset):
        if self.value() == "featured":
            return queryset.filter(is_featured=True)
        elif self.value() == "not":
            return queryset.filter(is_featured=False)


class EventSourceFilter(admin.SimpleListFilter):
    title = _("source")
    parameter_name = "event_source"

    def lookups(self, request, model_admin):
        return (
            ("input", _("Manual input")),
            ("gdacs", _("GDACs scraper")),
            ("who", _("WHO scraper")),
            ("report_ingest", _("Field report ingest")),
            ("report_admin", _("Field report admin")),
            ("appeal_admin", _("Appeals admin")),
            ("unknown", _("Unknown automated")),
        )

    def queryset(self, request, queryset):
        if self.value() == "input":
            return queryset.filter(auto_generated=False)
        elif self.value() == "gdacs":
            return queryset.filter(auto_generated_source=SOURCES["gdacs"])
        elif self.value() == "who":
            return queryset.filter(auto_generated_source__startswith="www.who.int")
        elif self.value() == "report_ingest":
            return queryset.filter(auto_generated_source=SOURCES["report_ingest"])
        elif self.value() == "report_admin":
            return queryset.filter(auto_generated_source=SOURCES["report_admin"])
        elif self.value() == "appeal_admin":
            return queryset.filter(auto_generated_source=SOURCES["appeal_admin"])
        elif self.value() == "unknown":
            return queryset.filter(auto_generated=True).filter(auto_generated_source__isnull=True)


class DisasterTypeAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    search_fields = ("name",)


class KeyFigureInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.KeyFigure


class SnippetInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.Snippet


class EventContactInline(admin.TabularInline):
    model = models.EventContact


class SituationReportInline(admin.TabularInline):
    model = models.SituationReport


class EventFeaturedDocumentInline(admin.TabularInline):
    model = models.EventFeaturedDocument


class EventLinkInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.EventLink


class EventAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = "countries__pk__in"
    region_in = "regions__pk__in"

    inlines = [
        KeyFigureInline,
        SnippetInline,
        EventContactInline,
        SituationReportInline,
        EventFeaturedDocumentInline,
        EventLinkInline,
    ]
    list_display = (
        "name",
        "ifrc_severity_level",
        "glide",
        "auto_generated",
        "auto_generated_source",
    )
    list_filter = [IsFeaturedFilter, EventSourceFilter]
    search_fields = (
        "name",
        "countries__name",
        "dtype__name",
    )
    autocomplete_fields = (
        "countries",
        "districts",
        "parent_event",
    )

    def appeals(self, instance):
        if getattr(instance, "appeals").exists():
            return format_html_join(
                mark_safe("<br />"), "{} - {}", ((appeal.code, appeal.name) for appeal in instance.appeals.all())
            )
        return mark_safe('<span class="errors">No related appeals</span>')

    appeals.short_description = "Appeals"

    # To add the 'Notify subscribers now' button
    # WikiJS links added
    change_form_template = "admin/emergency_change_form.html"
    change_list_template = "admin/emergency_change_list.html"

    # Overwriting readonly fields for Edit mode
    def changeform_view(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            self.readonly_fields = (
                "appeals",
                "field_reports",
                "auto_generated_source",
                "parent_event",
            )
        else:
            self.readonly_fields = (
                "appeals",
                "field_reports",
                "auto_generated_source",
            )

        return super(EventAdmin, self).changeform_view(request, *args, **kwargs)

    # Evaluate if the regular 'Save' or 'Notify subscribers now' button was pushed
    def response_change(self, request, obj):
        if "_notify-subscribers" in request.POST and request.user.is_superuser:
            notif_class = Notify()
            try:
                notif_class.notify(
                    records=[obj], rtype=RecordType.FOLLOWED_EVENT, stype=SubscriptionType.NEW, uid=request.user.id
                )
                self.message_user(request, "Successfully notified subscribers.")
            except Exception:
                self.message_user(request, "Could not notify subscribers.", level=messages.ERROR)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            # Fetch original object from DB to compare
            original = models.Event.objects.get(pk=obj.pk)

            severity_changed = original.ifrc_severity_level != obj.ifrc_severity_level
            update_date_changed = original.ifrc_severity_level_update_date != obj.ifrc_severity_level_update_date

            if severity_changed and not update_date_changed:
                messages.error(request, "You must update the 'IFRC Severity Level Update Date' when changing the severity level.")
                raise ValidationError("Cannot change severity level without updating the update date.")

            if severity_changed and update_date_changed:
                models.EventSeverityLevelHistory.objects.create(
                    event=obj,
                    ifrc_severity_level=obj.ifrc_severity_level,
                    ifrc_severity_level_update_date=obj.ifrc_severity_level_update_date,
                    created_by=request.user,
                )

        super().save_model(request, obj, form, change)

    def field_reports(self, instance):
        if getattr(instance, "field_reports").exists():
            return format_html_join(
                mark_safe("<br />"), "{} - {}", ((report.pk, report.summary) for report in instance.field_reports.all())
            )
        return mark_safe('<span class="errors">No related field reports</span>')

    field_reports.short_description = "Field Reports"


class GdacsAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = "countries__pk__in"
    region_in = None
    search_fields = ("title",)


class ActionsTakenInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.ActionsTaken


class SourceInline(admin.TabularInline):
    model = models.Source


class FieldReportContactInline(admin.TabularInline):
    model = models.FieldReportContact


class FieldReportAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):

    def assist(self, obj):
        return "+" if obj.ns_request_assistance else ""

    assist.boolean = ""
    country_in = "countries__pk__in"
    region_in = "regions__pk__in"

    inlines = [ActionsTakenInline, SourceInline, FieldReportContactInline]
    list_display = (
        "summary",
        "event",
        "created_at",
        "assist",
        "visibility",
    )
    list_select_related = ("event",)
    search_fields = (
        "countries__name",
        "regions__label",
        "summary",
    )
    autocomplete_fields = (
        "user",
        "dtype",
        "event",
        "countries",
        "districts",
    )

    readonly_fields = ("report_date", "created_at", "updated_at", "summary", "fr_num")
    list_filter = [MembershipFilter, "ns_request_assistance"]
    actions = [
        "create_events",
        "export_field_reports",
    ]
    # WikiJS links added
    change_form_template = "admin/fieldreport_change_form.html"
    change_list_template = "admin/fieldreport_change_list.html"

    def create_events(self, request, queryset):
        for report in queryset:
            event = models.Event.objects.create(
                name=report.summary,
                dtype=getattr(report, "dtype"),
                disaster_start_date=getattr(report, "created_at"),
                auto_generated=True,
                auto_generated_source=SOURCES["report_admin"],
            )
            if getattr(report, "countries").exists():
                for country in report.countries.all():
                    event.countries.add(country)
            if getattr(report, "regions").exists():
                for region in report.regions.all():
                    event.regions.add(region)
            report.event = event
            report.save()
        self.message_user(request, "%s emergency object(s) created" % queryset.count())

    create_events.short_description = "Create emergencies from selected reports"

    def export_field_reports(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        timestr = time.strftime("%Y%m%d-%H%M%S")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=FieldReports_export_{}.csv".format(timestr)
        writer = csv.writer(response)

        writer.writerow(field_names)

        for fr in queryset:
            writer.writerow([getattr(fr, field) for field in field_names])
        return response

    export_field_reports.short_description = "Export selected Field Reports to CSV"

    def get_actions(self, request):
        actions = super(FieldReportAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions["export_field_reports"]
        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request))
        if (
            models.CountryOfFieldReportToReview.objects.filter(country=request.user.profile.country).exists()
            and not request.user.is_superuser
        ):
            fields.append("visibility")
        return fields


class ExternalPartnerAdmin(CompareVersionAdmin, TranslationAdmin):
    model = models.ExternalPartner


class SupportedActivityAdmin(CompareVersionAdmin, TranslationAdmin):
    model = models.SupportedActivity


class ActionAdmin(CompareVersionAdmin, TranslationAdmin):
    form = ActionForm
    list_display = (
        "__str__",
        "field_report_types",
        "organizations",
        "category",
    )


class AppealDocumentInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.AppealDocument


class GeneralDocumentInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.GeneralDocument


class AppealAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):

    @admin.display(description="Force history save")
    def force_history_save(self, obj):
        return obj._force_history_save

    form = AppealForm
    force_history_save.boolean = False
    country_in = "country__pk__in"
    region_in = "region__pk__in"
    inlines = [AppealDocumentInline]
    list_display = (
        "code",
        "name",
        "atype",
        "needs_confirmation",
        "event",
        "start_date",
    )
    list_select_related = ("event",)
    search_fields = (
        "code",
        "name",
    )
    readonly_fields = ("region",)
    list_filter = [HasRelatedEventFilter, AppealTypeFilter]
    actions = ["create_events", "confirm_events"]
    autocomplete_fields = (
        "event",
        "country",
    )

    # WikiJS links added
    change_form_template = "admin/appeal_change_form.html"
    change_list_template = "admin/appeal_change_list.html"

    def create_events(self, request, queryset):
        for appeal in queryset:
            event = models.Event.objects.create(
                title=appeal.name,
                dtype=getattr(appeal, "dtype"),
                disaster_start_date=getattr(appeal, "start_date"),
                auto_generated=True,
                auto_generated_source=SOURCES["appeal_admin"],
            )
            if appeal.country is not None:
                event.countries.add(appeal.country)
            if appeal.region is not None:
                event.regions.add(appeal.region)
            appeal.event = event
            appeal.save()
        self.message_user(request, "%s emergency object(s) created" % queryset.count())

    create_events.short_description = "Create emergencies from selected appeals"

    def confirm_events(self, request, queryset):
        errors = []
        for appeal in queryset:
            if not appeal.needs_confirmation or not appeal.event:
                errors.append(appeal.code)
        if len(errors):
            self.message_user(
                request,
                "%s %s not have an unconfirmed event." % (", ".join(errors), "does" if len(errors) == 1 else "do"),
                level=messages.ERROR,
            )
        else:
            for appeal in queryset:
                appeal.needs_confirmation = False
                appeal.save()

    confirm_events.short_description = "Confirm emergencies as correct"

    def save_model(self, request, obj, form, change):
        if obj.country:
            obj.region = obj.country.region
        obj._force_history_save = form.cleaned_data.get("force_history_save", False)
        super().save_model(request, obj, form, change)


class AppealDocumentAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    @admin.display(ordering=Concat("appeal", Value(","), "name"))
    def appeal_document_label(self, obj):
        return "%s - %s" % (obj.appeal, obj.name)

    country_in = "appeal__country__in"
    region_in = "appeal__region__in"
    list_display = ("appeal_document_label", "description", "iso", "type", "created_at")
    search_fields = ("name", "appeal__code", "appeal__name", "description", "iso__name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("appeal")


class AppealDocumentTypeAdmin(CompareVersionAdmin):
    model = models.AppealDocumentType
    list_display = ("name", "id", "public_site_or_fednet")
    readonly_fields = ("id",)
    search_fields = ("name", "id")


class AppealFilterAdmin(CompareVersionAdmin):
    list_display = ("name", "value")
    search_fields = ("name", "value")


class UserCountryAdmin(CompareVersionAdmin):
    list_display = ("user", "country")
    # search_fields = ('user','country')
    model = models.UserCountry
    autocomplete_fields = (
        "user",
        "country",
    )


class UserRegionAdmin(CompareVersionAdmin):
    list_display = ["user", "get_firstname", "get_lastname", "get_email", "region"]

    def get_firstname(self, obj):
        return obj.user.first_name

    get_firstname.short_description = "First name"
    get_firstname.admin_order_field = "user__first_name"

    def get_lastname(self, obj):
        return obj.user.last_name

    get_lastname.short_description = "Last name"
    get_lastname.admin_order_field = "user__last_name"

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"

    # search_fields = ('user','country')
    model = models.UserRegion


class GeneralDocumentAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    search_fields = ("name", "document")


class CountryKeyFigureInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.CountryKeyFigure


class CountryDirectoryInline(admin.TabularInline):
    model = models.CountryDirectory


class RegionKeyFigureInline(admin.TabularInline):
    model = models.RegionKeyFigure


class CountrySnippetInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.CountrySnippet


class RegionSnippetInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.RegionSnippet
    verbose_name_plural = "Regional Snippets shown in Additional Tab"
    extra = 1


class RegionEmergencySnippetInline(admin.StackedInline, TranslationInlineModelAdmin):
    model = models.RegionEmergencySnippet
    verbose_name_plural = "Snippets shown in Operations / Emergencies Tab"
    extra = 1


class RegionProfileSnippetInline(admin.StackedInline, TranslationInlineModelAdmin):
    model = models.RegionProfileSnippet
    verbose_name_plural = "Snippets shown in Regional Profile Tab"
    extra = 1


class RegionPreparednessSnippetInline(admin.StackedInline, TranslationInlineModelAdmin):
    model = models.RegionPreparednessSnippet
    verbose_name_plural = "Snippets shown in Preparedness Tab"
    extra = 1


class CountryLinkInline(admin.TabularInline):
    model = models.CountryLink


class RegionLinkInline(admin.TabularInline):
    model = models.RegionLink


class CountryContactInline(admin.TabularInline):
    model = models.CountryContact


class CountryKeyDocumentInline(admin.TabularInline):
    model = models.CountryKeyDocument


class CountryICRCPresenceInline(admin.TabularInline):
    model = models.CountryICRCPresence


class RegionContactInline(admin.TabularInline):
    model = models.RegionContact


class IsDeprecatedFilter(admin.SimpleListFilter):
    title = "is deprecated"
    parameter_name = "is_deprecated"

    def lookups(self, request, model_admin):

        return (
            (False, "No"),
            (True, "Yes"),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(is_deprecated=self.value())
        return queryset


class CountryIsDeprecatedFilter1(IsDeprecatedFilter):
    title = "Country is deprecated"
    parameter_name = "admin1__country__is_deprecated"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(country__is_deprecated=self.value())
        return queryset


class DistrictAdmin(geoadmin.OSMGeoAdmin, CompareVersionAdmin, RegionRestrictedAdmin):

    country_in = "country__pk__in"
    region_in = "country__region__in"
    search_fields = (
        "name",
        "country__name",
    )
    list_display = ("__str__", "code")
    list_filter = (IsDeprecatedFilter, CountryIsDeprecatedFilter1, "country")
    modifiable = True


class NSDInitiativesAdmin(admin.TabularInline):
    model = models.NSDInitiatives


class CountryCapacityStrengtheningAdmin(admin.TabularInline):
    model = models.CountryCapacityStrengthening


class CountryOrganizationalCapacityAdmin(admin.TabularInline):
    model = models.CountryOrganizationalCapacity


class CountrySupportingPartnerAdmin(admin.TabularInline):
    model = models.CountrySupportingPartner


class CountryAdmin(geoadmin.OSMGeoAdmin, CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = "pk__in"
    list_filter = ("record_type", "in_search", "independent", "disputed")
    list_display = ("__str__", "record_type", "iso3")
    region_in = "region__pk__in"
    list_editable = ("record_type",)
    search_fields = ("name",)
    modifiable = True
    inlines = [
        CountryKeyFigureInline,
        CountrySnippetInline,
        CountryLinkInline,
        CountryContactInline,
        CountryDirectoryInline,
        CountryKeyDocumentInline,
        NSDInitiativesAdmin,
        CountryCapacityStrengtheningAdmin,
        CountryOrganizationalCapacityAdmin,
        CountrySupportingPartnerAdmin,
        CountryICRCPresenceInline,
    ]
    exclude = ("key_priorities",)


class RegionAdmin(geoadmin.OSMGeoAdmin, CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = None
    region_in = "pk__in"
    inlines = [
        RegionKeyFigureInline,
        RegionSnippetInline,
        RegionEmergencySnippetInline,
        RegionProfileSnippetInline,
        RegionPreparednessSnippetInline,
        RegionLinkInline,
        RegionContactInline,
    ]
    search_fields = ("name",)
    modifiable = True


class Admin1IsDeprecatedFilter(IsDeprecatedFilter):
    title = "Admin1 is deprecated"
    parameter_name = "admin1__is_deprecated"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(admin1__is_deprecated=self.value())
        return queryset


class CountryIsDeprecatedFilter2(IsDeprecatedFilter):
    title = "Country is deprecated"
    parameter_name = "admin1__country__is_deprecated"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(admin1__country__is_deprecated=self.value())
        return queryset


class Admin2Admin(geoadmin.OSMGeoAdmin, CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ("name", "admin1__country__name")
    list_filter = (IsDeprecatedFilter, Admin1IsDeprecatedFilter, CountryIsDeprecatedFilter2)
    modifiable = True


class UserProfileAdmin(CompareVersionAdmin):
    search_fields = (
        "user__username",
        "user__email",
        "country__name",
    )
    list_filter = (
        ("country__region", RelatedDropdownFilter),
        ("country", RelatedDropdownFilter),
        ("limit_access_to_guest"),
    )
    actions = ["export_selected_users"]
    readonly_fields = ("last_frontend_login",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def export_selected_users(self, request, queryset):
        meta = self.model._meta
        prof_field_names = [field.name for field in meta.fields]
        user_field_names = [field.name for field in models.User._meta.fields if field.name != "password"]
        timestr = time.strftime("%Y%m%d-%H%M%S")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=Users_export_{}.csv".format(timestr)
        writer = csv.writer(response)

        writer.writerow(prof_field_names + user_field_names + ["groups"])

        for prof in queryset:

            user_model = models.User.objects.get(id=prof.user_id)
            user_groups = list(user_model.groups.values_list("name", flat=True))
            user_groups_string = ", ".join(user_groups) if user_groups else ""

            writer.writerow(
                [getattr(prof, field) for field in prof_field_names]
                + [getattr(user_model, field) for field in user_field_names]
                + [user_groups_string]
            )
        return response

    export_selected_users.short_description = "Export selected Users with their Profiles"

    def get_actions(self, request):
        actions = super(UserProfileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions["export_selected_users"]
        return actions


class SituationReportAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = (
        "name",
        "event__name",
    )
    list_display = (
        "name",
        "link_to_event",
        "type",
        "created_at",
        "visibility",
    )
    country_in = "event__countries__in"
    region_in = "event__regions__in"
    autocomplete_fields = ("event",)
    readonly_fields = ("created_at",)

    # WikiJS links added
    change_form_template = "admin/situationreport_change_form.html"
    change_list_template = "admin/situationreport_change_list.html"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("type", "event")

    def link_to_event(self, obj):
        link = reverse("admin:api_event_change", args=[obj.event.id])  # model name has to be lowercase
        return format_html('<a href="{}" style="font-weight: 600;">{}</a>', link, obj.event.name)

    link_to_event.allow_tags = True


class SituationReportTypeAdmin(CompareVersionAdmin):
    search_fields = ("type",)


@admin.action(description="Set selected cronjob records to acknowleged status")
def acknowledge(modeladmin, request, queryset):
    queryset.update(status=-2)


class CronJobAdmin(CompareVersionAdmin):
    list_display = ("name", "created_at", "num_result", "status")
    search_fields = (
        "name",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "message_display",
    )
    list_filter = ("status", "name")
    actions = [acknowledge]

    def message_display(self, obj):
        style_class = {
            models.CronJobStatus.WARNED: "warning",
            models.CronJobStatus.ERRONEOUS: "error",
        }.get(obj.status, "success")
        if obj.message:
            return mark_safe(
                f"""
                <ul class="messagelist" style="margin-left: 0px;">
                    <li class="{style_class}"><pre>{obj.message}</pre></li>
                </ul>
                """
            )


class EmergencyOperationsBaseAdmin(CompareVersionAdmin):
    search_fields = (
        "file_name",
        "raw_file_name",
        "appeal_number",
    )
    list_display = (
        "file_name",
        "raw_file_name",
        "raw_file_url",
        "appeal_number",
        "is_validated",
    )
    actions = ["export_all", "export_selected"]
    document_type = None

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.get_fields() if field.name.startswith("raw_")]

    def get_fields(self, request, obj=None):
        readonly_fields = self.get_readonly_fields(request, obj)
        return ["is_validated", "raw_file_url"] + [(f[4:], f) for f in readonly_fields if f != "raw_file_url"]

    def export_selected(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name.startswith("raw_")]
        field_names_without_raw = [name[4:] for name in field_names]
        timestr = time.strftime("%Y%m%d-%H%M%S")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={self.document_type}_selected_list_{timestr}.csv"
        writer = csv.writer(response)

        first_row = [""]
        first_row.extend(field_names_without_raw)
        writer.writerow(first_row)

        counter = 0
        for fr in queryset:
            new_row = [counter]
            new_row.extend([getattr(fr, field) for field in field_names if field != ""])
            writer.writerow(new_row)
            counter += 1
        return response

    export_selected.short_description = "Export selected document(s) to CSV"

    def export_all(self, request, queryset):
        qset = self.model.objects.all()
        field_names = [field.name for field in qset.model._meta.fields if field.name.startswith("raw_")]
        field_names_without_raw = [name[4:] for name in field_names]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={self.document_type}.csv"
        writer = csv.writer(response)

        first_row = [""]
        first_row.extend(field_names_without_raw)
        writer.writerow(first_row)

        counter = 0
        for fr in qset:
            new_row = [counter]
            new_row.extend([getattr(fr, field) for field in field_names if field != ""])
            writer.writerow(new_row)
            counter += 1
        return response

    export_all.short_description = "Export all documents to CSV (select one before for it to work)"


class EmergencyOperationsDatasetAdmin(EmergencyOperationsBaseAdmin):
    document_type = "epoa"


class EmergencyOperationsPeopleReachedAdmin(EmergencyOperationsBaseAdmin):
    document_type = "ou"


class EmergencyOperationsFRAdmin(EmergencyOperationsBaseAdmin):
    document_type = "fr"


class EmergencyOperationsEAAdmin(EmergencyOperationsBaseAdmin):
    document_type = "ea"


class MainContactAdmin(CompareVersionAdmin):
    list_display = ("extent", "name", "email")
    search_fields = ("name", "email")


# Global view of Revisions, not that informational, maybe needed in the future
# class RevisionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'comment', 'date_created')
#     search_fields = ('user__username', 'comment')
#     date_hierarchy = ('date_created')
#     list_display_links = None


class AuthLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "action", "username"]
    list_filter = ["action"]
    search_fields = ["action", "username"]
    list_display_links = None

    def has_add_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class ReversionDifferenceLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "action", "object_type", "object_name", "object_id", "changed_from", "changed_to")
    list_filter = ("action", "object_type")
    search_fields = ("username", "object_name", "object_type", "changed_from", "changed_to")
    list_display_links = None

    def has_add_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class CountryOfFieldReportToReviewAdmin(admin.ModelAdmin):
    list_display = ("country",)

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return request.user.is_superuser

    @classmethod
    def has_view_permission(cls, request, obj=None):
        return request.user.is_superuser

    @classmethod
    def has_change_permission(cls, request, obj=None):
        return request.user.is_superuser

    @classmethod
    def has_add_permission(cls, request, obj=None):
        return request.user.is_superuser


@admin.register(models.EventSeverityLevelHistory)
class EventSeverityLevelHistoryAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ["event", "ifrc_severity_level", "created_by", "created_at"]
    autocomplete_fields = (
        "event",
        "created_by",
    )


@admin.register(models.Export)
class ExportTokenAdmin(admin.ModelAdmin):
    pass


try:
    admin.site.unregister(Permission)
except admin.sites.NotRegistered:
    pass

# Rename built-in Permission model for admin menu/link
Permission._meta.verbose_name = _("Users per permission")
Permission._meta.verbose_name_plural = _("Users per permission")


@admin.register(Permission)
class PermissionReportAdmin(admin.ModelAdmin):
    # Show the menu entry, but route to the Users-per-permission report.
    def has_module_permission(self, request):
        from api.admin_reports import _user_has_access

        return _user_has_access(request.user)

    def has_view_permission(self, request, obj=None):
        from api.admin_reports import _user_has_access

        return _user_has_access(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from api.admin_reports import users_per_permission_view

        return users_per_permission_view(request)


admin.site.register(models.DisasterType, DisasterTypeAdmin)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.GDACSEvent, GdacsAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.District, DistrictAdmin)
admin.site.register(models.Admin2, Admin2Admin)
admin.site.register(models.Appeal, AppealAdmin)
admin.site.register(models.AppealDocument, AppealDocumentAdmin)
admin.site.register(models.AppealDocumentType, AppealDocumentTypeAdmin)
admin.site.register(models.AppealFilter, AppealFilterAdmin)
admin.site.register(models.GeneralDocument, GeneralDocumentAdmin)
admin.site.register(models.FieldReport, FieldReportAdmin)
admin.site.register(models.ExternalPartner, ExternalPartnerAdmin)
admin.site.register(models.SupportedActivity, SupportedActivityAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Profile, UserProfileAdmin)
admin.site.register(models.SituationReport, SituationReportAdmin)
admin.site.register(models.SituationReportType, SituationReportTypeAdmin)
admin.site.register(models.EmergencyOperationsDataset, EmergencyOperationsDatasetAdmin)
admin.site.register(models.EmergencyOperationsPeopleReached, EmergencyOperationsPeopleReachedAdmin)
admin.site.register(models.EmergencyOperationsFR, EmergencyOperationsFRAdmin)
admin.site.register(models.EmergencyOperationsEA, EmergencyOperationsEAAdmin)
admin.site.register(models.CronJob, CronJobAdmin)
admin.site.register(models.AuthLog, AuthLogAdmin)
admin.site.register(models.ReversionDifferenceLog, ReversionDifferenceLogAdmin)
admin.site.register(models.MainContact, MainContactAdmin)
admin.site.register(models.UserCountry, UserCountryAdmin)
admin.site.register(models.UserRegion, UserRegionAdmin)
admin.site.register(models.CountryOfFieldReportToReview, CountryOfFieldReportToReviewAdmin)
# admin.site.register(Revision, RevisionAdmin)

admin.site.site_url = settings.GO_WEB_URL
admin.widgets.RelatedFieldWidgetWrapper.template_name = "related_widget_wrapper.html"
