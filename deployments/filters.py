from functools import reduce

import django_filters as filters
from django.contrib.auth.models import User
from django.db.models import F, Q

from api.models import Country, Event, Region

from .models import (
    ERU,
    EmergencyProject,
    EmergencyProjectActivitySector,
    ERUOwner,
    ERUType,
    OperationTypes,
    ProgrammeTypes,
    Project,
    Sector,
    SectorTag,
    Statuses,
)


class ProjectFilter(filters.FilterSet):
    budget_amount = filters.NumberFilter(field_name="budget_amount", lookup_expr="exact")
    country = filters.ModelMultipleChoiceFilter(
        field_name="project_country", queryset=Country.objects.all(), widget=filters.widgets.CSVWidget, method="filter_countries"
    )
    user = filters.ModelChoiceFilter(
        field_name="user",
        queryset=User.objects.all(),
    )
    country_iso3 = filters.ModelMultipleChoiceFilter(
        label="Country ISO3",
        field_name="project_country__iso3",
        method="filter_countries_iso3",
        to_field_name="iso3",
        widget=filters.widgets.CSVWidget,
        queryset=Country.objects.filter(iso3__isnull=False).all(),
    )
    region = filters.ModelMultipleChoiceFilter(
        label="Region", queryset=Region.objects.all(), widget=filters.widgets.CSVWidget, method="filter_regions"
    )
    operation_type = filters.MultipleChoiceFilter(choices=OperationTypes.choices, widget=filters.widgets.CSVWidget)
    programme_type = filters.MultipleChoiceFilter(choices=ProgrammeTypes.choices, widget=filters.widgets.CSVWidget)
    primary_sector = filters.ModelMultipleChoiceFilter(
        label="Sector", queryset=Sector.objects.all(), widget=filters.widgets.CSVWidget
    )
    secondary_sectors = filters.ModelMultipleChoiceFilter(
        label="SectorTag", queryset=SectorTag.objects.all(), widget=filters.widgets.CSVWidget
    )
    status = filters.MultipleChoiceFilter(choices=Statuses.choices, widget=filters.widgets.CSVWidget)
    # Supporting/Receiving NS Filters (Multiselect)
    reporting_ns = filters.ModelMultipleChoiceFilter(queryset=Country.objects.all(), widget=filters.widgets.CSVWidget)
    exclude_within = filters.BooleanFilter(
        label="Exclude projects with same country and Reporting NS", field_name="exclude_within", method="filter_exclude_within"
    )

    def filter_exclude_within(self, queryset, name, value):
        """
        Exclude projects which have same country and Reporting NS
        """
        if value:
            return queryset.exclude(reporting_ns=F("project_country"))
        return queryset

    def filter_countries_iso3(self, queryset, name, value):
        if value:
            return queryset.filter(Q(project_country__in=value) | Q(project_districts__country__in=value)).distinct()
        return queryset

    def filter_countries(self, queryset, name, country):
        if len(country):
            return queryset.filter(Q(project_country__in=country) | Q(project_districts__country__in=country)).distinct()
        return queryset

    def filter_regions(self, queryset, name, regions):
        if len(regions):
            return queryset.filter(
                Q(project_country__region__in=regions) | Q(project_districts__country__region__in=regions)
            ).distinct()
        return queryset

    class Meta:
        model = Project
        fields = [
            "country",
            "budget_amount",
            "start_date",
            "end_date",
            "project_districts",
            "reporting_ns",
            "programme_type",
            "status",
            "primary_sector",
            "operation_type",
            "exclude_within",
            "country_iso3",
            "user",
        ]


class EmergencyProjectFilter(filters.FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=EmergencyProject.ActivityStatus.choices,
    )
    activity_lead = filters.MultipleChoiceFilter(
        choices=EmergencyProject.ActivityLead.choices,
    )
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())
    country_iso3 = filters.ModelMultipleChoiceFilter(
        label="Country ISO3",
        field_name="country__iso3",
        method="filter_countries_iso3",
        widget=filters.widgets.CSVWidget,
        to_field_name="iso3",
        queryset=Country.objects.filter(iso3__isnull=False).all(),
    )
    reporting_ns = filters.ModelMultipleChoiceFilter(field_name="reporting_ns", queryset=Country.objects.all())
    event = filters.ModelMultipleChoiceFilter(field_name="event", queryset=Event.objects.all())
    deployed_eru = filters.ModelMultipleChoiceFilter(field_name="deployed_eru", queryset=ERU.objects.all())
    sector = filters.ModelMultipleChoiceFilter(
        label="sector", field_name="activities__sector", queryset=EmergencyProjectActivitySector.objects.all()
    )
    user = filters.ModelChoiceFilter(
        field_name="created_by",
        queryset=User.objects.all(),
    )

    class Meta:
        model = EmergencyProject
        fields = {
            "start_date": ("exact", "gt", "gte", "lt", "lte"),
        }

    def filter_countries_iso3(self, queryset, name, value):
        if value:
            return queryset.filter(Q(country__in=value) | Q(districts__country__in=value)).distinct()
        return queryset


class ERUOwnerFilter(filters.FilterSet):
    eru_type = filters.MultipleChoiceFilter(
        choices=ERUType.choices, label="eru_type", widget=filters.widgets.CSVWidget, method="filter_noop"
    )
    available = filters.BooleanFilter(method="filter_noop", label="available")

    class Meta:
        model = ERUOwner
        fields = ()

    def filter_noop(self, qs, name, value, *_):
        return qs

    @property
    def qs(self):
        qs = super().qs
        eru_type = self.form.cleaned_data.get("eru_type")
        available = self.form.cleaned_data.get("available")
        eru_qs = ERU.objects.all()
        if eru_type:
            eru_qs = eru_qs.filter(type__in=eru_type)
        if available is not None:
            eru_qs = eru_qs.filter(available=available)
        return qs.filter(eru__in=eru_qs).distinct()
