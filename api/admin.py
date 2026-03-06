import csv
import json
import time

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, User
from django.contrib.gis import admin as geoadmin
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Concat
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
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
from notifications.notification import send_notification

from .forms import ActionForm

# from reversion.models import Revision

CC_COLOR_MAP = {
    0: "#C8A600",
    1: "#C56A00",
    2: "#B00020",
}
CC_DOT_TEMPLATE = '<span style="color: {}; font-size: 1.4em;">●</span>'


def format_cc_dot(level):
    color = CC_COLOR_MAP.get(level)
    if not color:
        return ""
    return format_html(CC_DOT_TEMPLATE, color)


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

    @admin.display(ordering="ifrc_severity_level_update_date")
    def level_updated_at(self, obj):
        return obj.ifrc_severity_level_update_date

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
        "severity_level_link",
        "level_updated_at",
        "cc_status",
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

    def _crisis_categorisation_link_data(self, obj):
        # If there are event countries missing a CC-by-country record, prefer sending the user
        # to the "add" form prefilled with the first missing country.
        event_country_ids = list(obj.countries.values_list("pk", flat=True))
        if event_country_ids:
            existing_country_ids = set(
                models.CrisisCategorisationByCountry.objects.filter(event=obj, country_id__in=event_country_ids).values_list(
                    "country_id", flat=True
                )
            )
            missing_country_id = next((cid for cid in event_country_ids if cid not in existing_country_ids), None)
            if missing_country_id is not None:
                return (
                    reverse("admin:api_crisiscategorisationbycountry_add")
                    + f"?event={obj.pk}"
                    + f"&country={missing_country_id}"
                    + f"&crisis_categorisation={obj.ifrc_severity_level}",
                    "Add crisis categorisation",
                )

        first_crisis_cat = models.CrisisCategorisationByCountry.objects.filter(event=obj).first()
        if first_crisis_cat:
            return (
                reverse("admin:api_crisiscategorisationbycountry_change", args=[first_crisis_cat.pk]),
                "Edit crisis categorisation",
            )

        return (
            reverse("admin:api_crisiscategorisationbycountry_add")
            + f"?event={obj.pk}"
            + f"&crisis_categorisation={obj.ifrc_severity_level}",
            "Add crisis categorisation",
        )

    def severity_level_link(self, obj):
        """Display severity level as a link to Crisis Categorisation"""
        url, title = self._crisis_categorisation_link_data(obj)

        severity_display = obj.get_ifrc_severity_level_display()
        severity_dot = format_cc_dot(obj.ifrc_severity_level)
        if severity_display and severity_dot:
            severity_display = format_html("{} {}", severity_dot, severity_display)
        return format_html('<a href="{}" title="{}">{}</a>', url, title, severity_display)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        if obj is None:
            return form

        field = form.base_fields.get("ifrc_severity_level")
        if not field:
            return form

        url, title = self._crisis_categorisation_link_data(obj)
        field.label = mark_safe(
            f'<a href="{url}" title="{title}">IFRC Severity level</a>'
            ' <span class="help-icon cc-help-icon ifrc-severity-help-icon" '
            'title="Click for more information" '
            'aria-label="IFRC Severity level help">ⓘ</span>'
            ' <div class="help-tooltip cc-help-tooltip ifrc-severity-help-tooltip" role="tooltip">'
            "Link to the crisis categorisation page belonging to this event.<br>"
            "If this is a multi-country event, you may want to select the country yourself from the "
            '<a target="_blank" href="/admin/api/crisiscategorisationbycountry/">list</a> or'
            ' add a new record <a target="_blank" href="/admin/api/crisiscategorisationbycountry/add/'
            f'?event={obj.pk}&crisis_categorisation={obj.ifrc_severity_level}">here</a>.<br>'
            "</div>"
        )
        return form

    severity_level_link.short_description = "Crisis Categorisation"
    severity_level_link.admin_order_field = "ifrc_severity_level"

    @admin.display(description="CC Status", ordering="_cc_status")
    def cc_status(self, obj):
        latest_cc = models.CrisisCategorisationByCountry.objects.filter(event=obj).order_by("-updated_at").first()
        if not latest_cc or latest_cc.status is None:
            return "-"
        return latest_cc.get_status_display()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_cc_status = (
            models.CrisisCategorisationByCountry.objects.filter(event=OuterRef("pk")).order_by("-updated_at").values("status")[:1]
        )
        return qs.annotate(
            _cc_status=Subquery(latest_cc_status),
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
    change_list_template = "admin/emergency_change_list_with_history.html"

    # Overwriting readonly fields for Edit mode
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if not request.user.is_superuser:
            self.readonly_fields = (
                "appeals",
                "field_reports",
                "auto_generated_source",
                "parent_event",
                "created_at",
                "updated_at",
            )
        else:
            self.readonly_fields = (
                "appeals",
                "field_reports",
                "auto_generated_source",
                "created_at",
                "updated_at",
            )

        # Set severity level from GET parameter
        if object_id and request.GET.get("set_ifrc_severity_level"):
            # Not good, because this way no history will be saved:
            try:
                severity_level = int(request.GET.get("set_ifrc_severity_level"))
                if severity_level in [0, 1, 2]:  # Validate it's a valid choice
                    obj = self.get_object(request, object_id)
                    if obj:
                        original = models.Event.objects.get(pk=obj.pk)
                        severity_changed = original.ifrc_severity_level != severity_level
                        if severity_changed:
                            new_update_date = timezone.now()
                            if (
                                original.ifrc_severity_level_update_date is not None
                                and original.ifrc_severity_level_update_date > new_update_date
                            ):
                                messages.error(request, "A severity level update date can not be earlier than the previous one.")
                            else:
                                obj.ifrc_severity_level = severity_level
                                obj.ifrc_severity_level_update_date = new_update_date
                                obj.save(update_fields=["ifrc_severity_level", "ifrc_severity_level_update_date"])
                                models.EventSeverityLevelHistory.objects.create(
                                    event=obj,
                                    ifrc_severity_level=original.ifrc_severity_level,
                                    ifrc_severity_level_update_date=original.ifrc_severity_level_update_date,
                                    created_by=request.user,
                                )
            except (ValueError, TypeError):
                pass

        return super(EventAdmin, self).changeform_view(request, object_id, form_url, extra_context)

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
                messages.error(
                    request, "You must update the 'IFRC Severity Level Update Date/Time' when changing the severity level."
                )
                raise ValidationError("Cannot change severity level without updating the update date/time.")

            if severity_changed and update_date_changed:
                if (
                    original.ifrc_severity_level_update_date is not None
                    and original.ifrc_severity_level_update_date > obj.ifrc_severity_level_update_date
                ):
                    messages.error(request, "A severity level update date can not be earlier than the previous one.")
                    raise ValidationError("A severity level update date can not be earlier than the previous one.")
                models.EventSeverityLevelHistory.objects.create(
                    event=obj,
                    ifrc_severity_level=original.ifrc_severity_level,
                    ifrc_severity_level_update_date=original.ifrc_severity_level_update_date,
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

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        # Check if we have a result list to process
        if hasattr(response, "context_data") and "cl" in response.context_data:
            cl = response.context_data["cl"]
            result_list = list(cl.result_list)
            expanded_results = []

            for event in result_list:
                # Add the main event row
                expanded_results.append(
                    {
                        "object": event,
                        "is_history": False,
                        "history_record": None,
                    }
                )

                # Add history rows if they exist
                history_records = models.EventSeverityLevelHistory.objects.filter(event=event).order_by(
                    "-ifrc_severity_level_update_date"
                )

                for history in history_records:
                    expanded_results.append(
                        {
                            "object": event,
                            "is_history": True,
                            "history_record": {
                                "date": (
                                    date_format(history.ifrc_severity_level_update_date, "N j, Y, g:i a")
                                    if history.ifrc_severity_level_update_date
                                    else ""
                                ),
                                "severity": history.get_ifrc_severity_level_display(),
                                "severity_value": history.ifrc_severity_level,
                            },
                        }
                    )

            # Convert to JSON for JavaScript

            response.context_data["expanded_results"] = json.dumps(expanded_results, default=str)

        return response

    class Media:
        js = ("js/event_severity_help.js",)


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

    @admin.display(description="Updated at", ordering="ifrc_severity_level_update_date")
    def updated_at(self, obj):
        return obj.ifrc_severity_level_update_date

    list_select_related = True
    list_display = ["event", "ifrc_severity_level", "created_by", "updated_at", "created_at"]
    autocomplete_fields = (
        "event",
        "created_by",
    )


class CrisisCategorisationByCountryAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_status(self):
        new_status = self.cleaned_data.get("status")
        if new_status is None:
            return new_status

        validated_status = int(models.CrisisCategorisationStatus.VALIDATED)
        original_status = getattr(self.instance, "status", None)

        # Only restrict transitions *to* VALIDATED (3) or above.
        is_transition_to_validated_or_above = new_status >= validated_status and new_status != original_status
        if not is_transition_to_validated_or_above:
            return new_status

        request = getattr(self, "request", None)
        if request is None:
            return new_status

        user = request.user
        allowed_group_names = [f"{i} Regional Admins" for i in range(5)]
        is_allowed = bool(getattr(user, "is_superuser", False) or user.groups.filter(name__in=allowed_group_names).exists())
        if not is_allowed:
            raise forms.ValidationError(_("Only superusers or Regional Admins (0-4) can set status to Validated or above."))

        notification_subject = "Crisis categorisation status updated"
        cc_id = self.instance.pk if self.instance.pk is not None else "new"
        notification_content = f"Crisis categorisation (id = {cc_id}) status was changed to {new_status}."
        notification_html = render_to_string(
            "design/generic_notification.html",
            {
                "count": 1,
                "records": [
                    {
                        "title": notification_subject,
                        "content": notification_content,
                        "resource_uri": settings.GO_WEB_URL,
                    }
                ],
                "subject": notification_subject,
                "hide_preferences": True,
                "frontend_url": settings.GO_WEB_URL,
            },
        )
        recipients = list(
            User.objects.filter(groups__name="Crisis Categorization Validator", is_active=True)
            .exclude(email__isnull=True)
            .exclude(email="")
            .values_list("email", flat=True)
            .distinct()
        )
        if recipients:
            send_notification(
                notification_subject,
                recipients,
                notification_html,
                f"Crisis categorisation status update - {cc_id} to {new_status}",
            )

        return new_status

    class Meta:
        model = models.CrisisCategorisationByCountry
        fields = "__all__"


@admin.register(models.CrisisCategorisationByCountry)
class CrisisCategorisationByCountryAdmin(admin.ModelAdmin):
    form = CrisisCategorisationByCountryAdminForm

    def get_form(self, request, obj=None, change=False, **kwargs):
        label = str(_("Crisis Categorisation Overview"))
        if obj and obj.event_id:
            iso2_codes = list(
                obj.event.countries.exclude(iso__isnull=True).exclude(iso="").values_list("iso", flat=True).order_by("iso")
            )
            if iso2_codes:
                iso_list = ", ".join(iso2_codes)
                cc_dot = format_cc_dot(obj.event.ifrc_severity_level)
                if cc_dot:
                    inner = format_html("{} {}", cc_dot, iso_list)
                else:
                    inner = iso_list
                label = format_html("<strong>{}</strong> ({})", label, inner)
        self.__class__.event_countries_overview.short_description = format_html("{}", label)

        base_form_class = super().get_form(request, obj, change=change, **kwargs)

        class FormWithRequest(base_form_class):
            def __init__(self, *args, **kwargs):
                kwargs["request"] = request
                super().__init__(*args, **kwargs)

        return FormWithRequest

    list_display = [
        "event",
        "country",
        "crisis_categorisation",
        "crisis_score",
        "status",
        "updated_at",
    ]
    list_filter = ["crisis_categorisation", "event"]
    list_select_related = ["event", "country"]
    search_fields = ["event__name", "country__name"]
    autocomplete_fields = ["event"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "event_countries_overview",
        "pre_crisis_vulnerability",
        "crisis_complexity",
        "scope_and_scale",
        "humanitarian_conditions",
        "capacity_and_response",
        # "pre_crisis_vulnerability_hazard_exposure_intermediate",
        # "pre_crisis_vulnerability_vulnerability_intermediate",
        # "pre_crisis_vulnerability_coping_mechanism_intermediate",
        # "crisis_complexity_humanitarian_access_acaps",
        # "scope_and_scale_number_of_affected_population",
        # "scope_and_scale_total_population_of_the_affected_area",
        # "scope_and_scale_percentage_affected_population",
        # "scope_and_scale_impact_index_inform",
        # "humanitarian_conditions_casualties_injrd_deaths_missing",
        # "humanitarian_conditions_severity",
        # "humanitarian_conditions_people_in_need",
        # "capacity_and_response_ifrc_international_staff",
        # "capacity_and_response_ifrc_national_staff",
        # "capacity_and_response_ifrc_total_staff",
        # "capacity_and_response_regional_office",
        # "capacity_and_response_ops_capacity_ranking",
        # "capacity_and_response_number_of_ns_staff",
        # "capacity_and_response_ratio_staff_volunteer",
        # "capacity_and_response_number_of_ns_volunteer",
        # "capacity_and_response_number_of_dref_ea_last_3_years",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is a "Change" – we do not allow to change the country
            return self.readonly_fields + ["event", "country"]
        return self.readonly_fields

    class Media:
        js = ("js/crisis_categorisation_headers.js",)

    def event_countries_overview(self, obj):
        """Display a table of all countries for this event with their crisis scores"""
        if not obj.event:
            return ""

        # Get all crisis categorisations for this event
        categorisations = (
            models.CrisisCategorisationByCountry.objects.filter(event=obj.event)
            .select_related("country")
            .order_by("country__name")
        )

        if not categorisations.exists():
            return mark_safe('<p style="color: #666;">No countries categorised for this event yet.</p>')

        # Build HTML table
        html = """
        <style>
            .crisis-overview-table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
                font-size: 12px;
            }
            .crisis-overview-table th {
                background: #417690;
                color: white;
                padding: 8px 10px;
                text-align: left;
                font-weight: 600;
                border: 1px solid #ddd;
            }
            .crisis-overview-table td {
                padding: 6px 10px;
                border: 1px solid #ddd;
                background: #fff;
            }
            .crisis-overview-table tr:nth-child(even) td {
                background: #f8f8f8;
            }
            .crisis-overview-table tr:hover td {
                background: #e8f4f8;
            }
            .crisis-overview-table tr.current-country td {
                background: #fffacd !important;
                font-weight: 600;
            }
            .cc-badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 3px;
                font-weight: 600;
                text-align: center;
                min-width: 70px;
            }
            .cc-yellow { background: #FFD700; color: #000; }
            .cc-orange { background: #FFA500; color: #000; }
            .cc-red { background: #DC143C; color: #fff; }

            .crisis-overview-table a {
                color: #0066cc;
                text-decoration: none;
            }
            .crisis-overview-table a:hover {
                text-decoration: underline;
            }

            /* Dark theme support */
            @media (prefers-color-scheme: dark) {
                .crisis-overview-table th {
                    background: #2b5468;
                    border-color: #444;
                }
                .crisis-overview-table td {
                    background: #2b2b2b;
                    border-color: #444;
                    color: #f0f0f0;
                }
                .crisis-overview-table tr:nth-child(even) td {
                    background: #333;
                }
                .crisis-overview-table tr:hover td {
                    background: #3a4d5c;
                }
                .crisis-overview-table tr.current-country td {
                    background: #4a4520 !important;
                    color: #ffd;
                }
                .crisis-overview-table a {
                    color: #6eb3ff;
                }
            }
        </style>
        <table class="crisis-overview-table">
            <thead>
                <tr>
                    <th>Country</th>
                    <th>CC</th>
                    <th>Crisis score</th>
                    <th>1. Pre-crisis vulnerability</th>
                    <th>2. Crisis complexity</th>
                    <th>3. Scope & scale</th>
                    <th>4. Humanitarian conditions</th>
                    <th>5. Capacity & response</th>
                </tr>
            </thead>
            <tbody>
        """

        total_count = categorisations.count()

        for cat in categorisations:
            cc_display = cat.get_crisis_categorisation_display() if cat.crisis_categorisation is not None else "-"
            cc_dot = format_cc_dot(cat.crisis_categorisation)
            if cc_display != "-" and cc_dot:
                cc_display = f"{cc_dot} {cc_display}"

            if total_count == 1 and obj.status and obj.status > 2 and cat.crisis_categorisation in [0, 1, 2]:
                event_url_base = f"../../../event/{obj.event.pk}/change/"
                finalise_url = f"{event_url_base}?set_ifrc_severity_level={cat.crisis_categorisation}"
                cc_display = (
                    f'{cc_display} (<a target="_blank" href="{finalise_url}" style="text-decoration: none;">'
                    "Approve as final"
                    "</a>)"
                )

            # Highlight current country
            row_class = "current-country" if cat.country == obj.country else ""
            change_url = f"../../{cat.pk}/change/"

            html += f"""
                <tr class="{row_class}">
                    <td><a href="{change_url}">{cat.country.name}</a></td>
                    <td>{cc_display}</td>
                    <td>{cat.crisis_score if cat.crisis_score else "-"}</td>
                    <td>{cat.pre_crisis_vulnerability if cat.pre_crisis_vulnerability else "-"}</td>
                    <td>{cat.crisis_complexity if cat.crisis_complexity else "-"}</td>
                    <td>{cat.scope_and_scale if cat.scope_and_scale else "-"}</td>
                    <td>{cat.humanitarian_conditions if cat.humanitarian_conditions else "-"}</td>
                    <td>{cat.capacity_and_response if cat.capacity_and_response else "-"}</td>
                </tr>
            """

        # Add final row with averages if there are multiple countries
        if total_count > 1:
            # Calculate averages
            def calc_avg(field_name):
                values = [getattr(cat, field_name) for cat in categorisations if getattr(cat, field_name) is not None]
                if values:
                    return round(sum(values) / len(values), 2)
                return "-"

            avg_crisis_score = calc_avg("crisis_score")
            avg_pre_crisis = calc_avg("pre_crisis_vulnerability")
            avg_crisis_complexity = calc_avg("crisis_complexity")
            avg_scope_scale = calc_avg("scope_and_scale")
            avg_humanitarian = calc_avg("humanitarian_conditions")
            avg_capacity = calc_avg("capacity_and_response")

            # Create links for Y, O, R to event page with severity level filters
            event_url_base = f"../../../event/{obj.event.pk}/change/"
            y_link = (
                f'<a target="_blank" href="{event_url_base}?set_ifrc_severity_level=0" style="text-decoration: none;">Yellow</a>'
            )
            o_link = (
                f'<a target="_blank" href="{event_url_base}?set_ifrc_severity_level=1" style="text-decoration: none;">Orange</a>'
            )
            r_link = (
                f'<a target="_blank" href="{event_url_base}?set_ifrc_severity_level=2" style="text-decoration: none;">Red</a>'
            )

            if obj.status > 2:
                finalize = f"Approve as {y_link} / {o_link} / {r_link}"
            else:
                finalize = "Get this categorisation validated."

            html += f"""
                <tr style="font-weight: 600; background: #f0f0f0 !important;">
                    <td>Summary</td>
                    <td>{finalize}</td>
                    <td>{avg_crisis_score}</td>
                    <td>{avg_pre_crisis}</td>
                    <td>{avg_crisis_complexity}</td>
                    <td>{avg_scope_scale}</td>
                    <td>{avg_humanitarian}</td>
                    <td>{avg_capacity}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return mark_safe(html)

    event_countries_overview.short_description = mark_safe("<strong>" + _("Crisis Categorisation Overview") + "</strong>")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "event",
                    "event_countries_overview",
                    "country",
                    "crisis_categorisation",
                    "crisis_score",
                )
            },
        ),
        (
            "1. Pre-Crisis Vulnerability",
            {
                "fields": (
                    "pre_crisis_vulnerability",
                    ("pre_crisis_vulnerability_hazard_exposure", "pre_crisis_vulnerability_hazard_exposure_comment"),
                    (
                        "pre_crisis_vulnerability_hazard_exposure_intermediate",
                        "pre_crisis_vulnerability_hazard_exposure_intermediate_comment",
                    ),
                    ("pre_crisis_vulnerability_vulnerability", "pre_crisis_vulnerability_vulnerability_comment"),
                    (
                        "pre_crisis_vulnerability_vulnerability_intermediate",
                        "pre_crisis_vulnerability_vulnerability_intermediate_comment",
                    ),
                    ("pre_crisis_vulnerability_coping_mechanism", "pre_crisis_vulnerability_coping_mechanism_comment"),
                    (
                        "pre_crisis_vulnerability_coping_mechanism_intermediate",
                        "pre_crisis_vulnerability_coping_mechanism_intermediate_comment",
                    ),
                )
            },
        ),
        (
            "2. Crisis Complexity",
            {
                "fields": (
                    "crisis_complexity",
                    ("crisis_complexity_humanitarian_access_score", "crisis_complexity_humanitarian_access_score_comment"),
                    ("crisis_complexity_humanitarian_access_acaps", "crisis_complexity_humanitarian_access_acaps_comment"),
                    ("crisis_complexity_government_response", "crisis_complexity_government_response_comment"),
                    ("crisis_complexity_media_attention", "crisis_complexity_media_attention_comment"),
                    ("crisis_complexity_ifrc_security_phase", "crisis_complexity_ifrc_security_phase_comment"),
                )
            },
        ),
        (
            "3. Scope & Scale",
            {
                "fields": (
                    "scope_and_scale",
                    (
                        "scope_and_scale_number_of_affected_population_score",
                        "scope_and_scale_number_of_affected_population_score_comment",
                    ),
                    (
                        "scope_and_scale_number_of_affected_population",
                        "scope_and_scale_number_of_affected_population_comment",
                    ),
                    (
                        "scope_and_scale_percentage_affected_population_score",
                        "scope_and_scale_percentage_affected_population_score_comment",
                    ),
                    (
                        "scope_and_scale_total_population_of_the_affected_area",
                        "scope_and_scale_total_population_of_the_affected_area_comment",
                    ),
                    (
                        "scope_and_scale_percentage_affected_population",
                        "scope_and_scale_percentage_affected_population_comment",
                    ),
                    ("scope_and_scale_impact_index_score", "scope_and_scale_impact_index_score_comment"),
                    ("scope_and_scale_impact_index_inform", "scope_and_scale_impact_index_inform_comment"),
                )
            },
        ),
        (
            "4. Humanitarian Conditions",
            {
                "fields": (
                    "humanitarian_conditions",
                    ("humanitarian_conditions_casualties_score", "humanitarian_conditions_casualties_score_comment"),
                    (
                        "humanitarian_conditions_casualties_injrd_deaths_missing",
                        "humanitarian_conditions_casualties_injrd_deaths_missing_comment",
                    ),
                    ("humanitarian_conditions_severity_score", "humanitarian_conditions_severity_score_comment"),
                    ("humanitarian_conditions_severity", "humanitarian_conditions_severity_comment"),
                    ("humanitarian_conditions_people_in_need_score", "humanitarian_conditions_people_in_need_score_comment"),
                    ("humanitarian_conditions_people_in_need", "humanitarian_conditions_people_in_need_comment"),
                )
            },
        ),
        (
            "5. Capacity & Response",
            {
                "fields": (
                    "capacity_and_response",
                    ("capacity_and_response_ifrc_capacity_score", "capacity_and_response_ifrc_capacity_score_comment"),
                    ("capacity_and_response_ifrc_international_staff", "capacity_and_response_ifrc_international_staff_comment"),
                    ("capacity_and_response_ifrc_national_staff", "capacity_and_response_ifrc_national_staff_comment"),
                    ("capacity_and_response_ifrc_total_staff", "capacity_and_response_ifrc_total_staff_comment"),
                    ("capacity_and_response_regional_office", "capacity_and_response_regional_office_comment"),
                    ("capacity_and_response_ops_capacity_score", "capacity_and_response_ops_capacity_score_comment"),
                    ("capacity_and_response_ops_capacity_ranking", "capacity_and_response_ops_capacity_ranking_comment"),
                    ("capacity_and_response_ns_staff_score", "capacity_and_response_ns_staff_score_comment"),
                    ("capacity_and_response_number_of_ns_staff", "capacity_and_response_number_of_ns_staff_comment"),
                    (
                        "capacity_and_response_ratio_staff_to_volunteer_score",
                        "capacity_and_response_ratio_staff_to_volunteer_score_comment",
                    ),
                    ("capacity_and_response_ratio_staff_volunteer", "capacity_and_response_ratio_staff_volunteer_comment"),
                    ("capacity_and_response_number_of_ns_volunteer", "capacity_and_response_number_of_ns_volunteer_comment"),
                    ("capacity_and_response_number_of_dref_score", "capacity_and_response_number_of_dref_score_comment"),
                    (
                        "capacity_and_response_number_of_dref_ea_last_3_years",
                        "capacity_and_response_number_of_dref_ea_last_3_years_comment",
                    ),
                    (
                        "capacity_and_response_presence_support_pns_in_country",
                        "capacity_and_response_presence_support_pns_in_country_comment",
                    ),
                )
            },
        ),
        (
            "––––––––––––––––––––",
            {"fields": ("commentary", "general_document", "status")},
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("event", "country")


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
