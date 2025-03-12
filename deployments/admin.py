import csv

from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.admin import helpers
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from reversion_compare.admin import CompareVersionAdmin

import deployments.models as models
from api.admin_classes import RegionRestrictedAdmin
from api.utils import Echo
from lang.admin import TranslationAdmin

from .forms import ProjectForm, ProjectImportForm


class ERUInline(admin.TabularInline):
    model = models.ERU
    autocomplete_fields = ("deployed_to", "event", "appeal")


class ERUOwnerAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = "national_society_country__in"
    region_in = "national_society_country__region__in"
    inlines = [ERUInline]
    autocomplete_fields = ("national_society_country",)
    search_fields = ("national_society_country__name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("national_society_country")


class SectorAdmin(CompareVersionAdmin, admin.ModelAdmin):
    model = models.Sector
    search_fields = ("title",)


class SectorTagAdmin(CompareVersionAdmin, admin.ModelAdmin):
    model = models.SectorTag
    search_fields = ("title",)


class MolnixTagGroupAdmin(CompareVersionAdmin, admin.ModelAdmin):
    model = models.MolnixTagGroup
    list_display = ["name", "molnix_id"]
    ordering = ("molnix_id",)
    search_fields = ("name",)


@admin.register(models.ERU)
class ERUAdmin(CompareVersionAdmin, admin.ModelAdmin):
    search_fields = ("national_society_country__name",)


class PersonnelAdmin(CompareVersionAdmin, TranslationAdmin):
    country_in = "country_from__in"
    region_in = "country_from__region__in"
    search_fields = (
        "name",
        "role",
        "type",
    )
    list_display = (
        "name",
        "role",
        "start_date",
        "end_date",
        "country_from",
        "deployment",
    )
    readonly_fields = ("molnix_id",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "country_from",
                "deployment__country_deployed_to",
                "deployment__region_deployed_to",
                "deployment__event_deployed_to",
            )
        )


class PersonnelInline(admin.TabularInline):

    def surge_alert_notification(self, obj):
        if obj.surge_alert:
            return "%s (%d)" % (obj.surge_alert.message, obj.surge_alert.id)
        return "-"

    model = models.Personnel
    # including surge_alert makes queries really, really heavy and timeout prone: instead of 20 queries it gives 13700.
    exclude = ("surge_alert", "molnix_tags")
    autocomplete_fields = (
        "country_from",
        "country_to",
    )
    readonly_fields = ("molnix_id", "surge_alert_notification")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "country_from",
                "country_to",
            )
        )
        # "deployedperson_ptr", "country_from", "country_to", "deployment", "surge_alert", "surge_alert__event")


class PersonnelDeploymentAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("country_deployed_to__name", "region_deployed_to__label", "event_deployed_to__name")
    autocomplete_fields = ("event_deployed_to", "appeal_deployed_to")
    inlines = [PersonnelInline]
    list_display = (
        "country_deployed_to",
        "region_deployed_to",
        "event_deployed_to",
        "comments",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("country_deployed_to", "region_deployed_to", "event_deployed_to", "appeal_deployed_to")
        )
        # .prefetch_related("personnel_set", "personnel_set__deployment", "appeal_deployed_to__event",
        # "personnel_set__deployment__event_deployed_to", "personnel_set__deployedperson_ptr", "personnel_set__country_from",
        # "personnel_set__country_to", "personnel_set__surge_alert", "personnel_set__surge_alert__event")


class PartnerSocietyActivityAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("activity",)


class PartnerSocietyDeploymentAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = "parent_society__in"
    region_in = "parent_society__region__in"
    autocomplete_fields = (
        "parent_society",
        "country_deployed_to",
        "district_deployed_to",
    )
    search_fields = (
        "activity__activity",
        "name",
        "role",
        "country_deployed_to__name",
        "parent_society__name",
        "district_deployed_to__name",
    )
    list_display = (
        "name",
        "role",
        "activity",
        "parent_society",
        "country_deployed_to",
        "start_date",
        "end_date",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("activity", "parent_society", "country_deployed_to")


class RegionalProjectAdmin(CompareVersionAdmin, TranslationAdmin):
    list_display = (
        "name",
        "created_at",
        "modified_at",
    )
    search_fields = ("name",)


class ProjectNSFilter(AutocompleteFilter):
    title = _("National Society")
    field_name = "reporting_ns"


class ProjectCountryFilter(AutocompleteFilter):
    title = _("Country")
    field_name = "project_country"


class ProjectAnnualSplitAdminInline(admin.TabularInline):
    model = models.AnnualSplit


class ProjectAdmin(CompareVersionAdmin, TranslationAdmin):
    form = ProjectForm
    reporting_ns_in = "country_from__in"
    search_fields = ("name",)
    list_filter = (
        ("reporting_ns", RelatedDropdownFilter),
        ("project_country", RelatedDropdownFilter),
    )
    autocomplete_fields = (
        "user",
        "reporting_ns",
        "project_country",
        "project_districts",
        "regional_project",
        "event",
        "dtype",
        "project_admin2",
    )
    inlines = [ProjectAnnualSplitAdminInline]

    class Media:  # Required by AutocompleteFilter
        pass

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("reporting_ns")

    def get_url_namespace(self, name, absolute=True):
        meta = self.model._meta
        namespace = f"{meta.app_label}_{meta.model_name}_{name}"
        return f"admin:{namespace}" if absolute else namespace

    # Add import button to changelist (Using extended admin/change_list.html)
    def changelist_view(self, request, extra_context={}):
        pi_meta = models.ProjectImport._meta
        extra_context["additional_addlinks"] = [
            {
                "namespace": self.get_url_namespace("bulk_import"),
                "label": gettext("New Import"),
            },
            {
                "namespace": f"admin:{pi_meta.app_label}_{pi_meta.model_name}_changelist",
                "label": gettext("Recent Imports"),
            },
            {
                "namespace": self.get_url_namespace("bulk_import_template"),
                "label": gettext("Import Template"),
            },
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        return [
            path("import/", self.admin_site.admin_view(self.bulk_import), name=self.get_url_namespace("bulk_import", False)),
            path(
                "import-template/",
                self.admin_site.admin_view(self.bulk_import_template),
                name=self.get_url_namespace("bulk_import_template", False),
            ),
        ] + super().get_urls()

    def bulk_import_template(self, request):
        rows = ProjectImportForm.generate_template()
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="project-import-template.csv"'
        return response

    def bulk_import(self, request):
        if request.method == "POST":
            form = ProjectImportForm(request.POST, request.FILES)
            if form.is_valid():
                form.handle_bulk_upload(request)
                return redirect(self.get_url_namespace("changelist"))
        form = ProjectImportForm()
        context = {
            **self.admin_site.each_context(request),
            "has_view_permission": self.has_change_permission(request),
            "app_label": self.model._meta.app_label,
            "title": "Import Projects",
            "opts": self.model._meta,
            "form": form,
            "adminform": helpers.AdminForm(
                form,
                list([(None, {"fields": form.base_fields})]),
                self.get_prepopulated_fields(request),
            ),
        }
        return render(
            request,
            "admin/import_form.html",
            context,
        )


class ProjectImportProjectInline(admin.TabularInline):
    model = models.ProjectImport.projects_created.through
    readonly_fields = ("project_link",)
    verbose_name_plural = _("Projects")
    max_num = 0
    show_change_link = True
    fieldsets = ((None, {"fields": ("project_link",)}),)

    def project_link(self, obj):
        meta = models.Project._meta
        url = reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=(obj.project_id,))
        return mark_safe(
            f"""
            <a target="_blank" href="{url}">{obj.project}</a>
        """
        )


class ProjectImportAdmin(admin.ModelAdmin):
    search_fields = ("file",)
    readonly_fields = (
        "id",
        "created_by",
        "created_at",
        "message_display",
        "file",
        "status",
    )
    list_display = ("created_by", "created_at", "status", "file")
    list_filter = ("created_at", "status")
    actions = None
    fieldsets = ((None, {"fields": ("created_by", "created_at", "file", "status", "message_display")}),)
    inlines = (ProjectImportProjectInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("projects_created", "created_by")

    def has_add_permission(self, requests, obj=None):
        return False

    def has_delete_permission(self, requests, obj=None):
        return False

    def message_display(self, obj):
        if obj.message:
            style_class = "error" if obj.status == models.ProjectImport.FAILURE else ""
            return mark_safe(
                f"""
                <ul class="messagelist" style="margin-left: 0px;"><li class="{style_class}">{obj.message}</li></ul>
            """
            )


class ERUReadinessAdmin(CompareVersionAdmin, admin.ModelAdmin):
    search_fields = ("eru_owner__national_society_country__name",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "eru_owner",
            )
            .prefetch_related(
                "eru_types",
            )
        )


# ----- Emergency Project ----- [Start]
class EmergencyProjectActivityActionSupplyInline(admin.TabularInline):
    model = models.EmergencyProjectActivityActionSupply


class EmergencyProjectActivityActionInline(admin.TabularInline):
    model = models.EmergencyProjectActivityAction


@admin.register(models.EmergencyProjectActivityAction)
class EmergencyProjectActivityActionAdmin(CompareVersionAdmin, admin.ModelAdmin):
    search_fields = ("title",)
    inlines = (EmergencyProjectActivityActionSupplyInline,)


@admin.register(models.EmergencyProjectActivitySector)
class EmergencyProjectActivitySectorAdmin(CompareVersionAdmin, admin.ModelAdmin):
    search_fields = ("title",)
    inlines = (EmergencyProjectActivityActionInline,)


class EmergencyProjectActivityInline(admin.TabularInline):
    model = models.EmergencyProjectActivity
    autocomplete_fields = (
        "sector",
        "action",
    )
    extra = 0


@admin.register(models.EmergencyProject)
class EmergencyProjectAdmin(CompareVersionAdmin, admin.ModelAdmin):
    search_fields = ("title",)
    autocomplete_fields = (
        "created_by",
        "modified_by",
        "event",
        "reporting_ns",
        "deployed_eru",
        "country",
        "districts",
        "admin2",
    )
    list_display = ["title", "event", "country", "reporting_ns"]
    inlines = (EmergencyProjectActivityInline,)


# ----- Emergency Project ----- [End]

admin.site.register(models.ERUOwner, ERUOwnerAdmin)
admin.site.register(models.PersonnelDeployment, PersonnelDeploymentAdmin)
admin.site.register(models.Personnel, PersonnelAdmin)
admin.site.register(models.PartnerSocietyDeployment, PartnerSocietyDeploymentAdmin)
admin.site.register(models.PartnerSocietyActivities, PartnerSocietyActivityAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.ProjectImport, ProjectImportAdmin)
admin.site.register(models.RegionalProject, RegionalProjectAdmin)
admin.site.register(models.ERUReadiness, ERUReadinessAdmin)
admin.site.register(models.ERUReadinessType)
admin.site.register(models.Sector, SectorAdmin)
admin.site.register(models.SectorTag, SectorTagAdmin)
admin.site.register(models.MolnixTagGroup, MolnixTagGroupAdmin)
