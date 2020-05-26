from functools import reduce
import django_filters as filters
from django.db.models import Q

from api.models import Region, Country
from .models import (
    OperationTypes,
    ProgrammeTypes,
    Sectors,
    SectorTags,
    Statuses,
    Project,
)


class ProjectFilter(filters.FilterSet):
    budget_amount = filters.NumberFilter(field_name='budget_amount', lookup_expr='exact')
    country = filters.CharFilter(label='Country ISO/ISO3', field_name='country', method='filter_countries')
    region = filters.ModelMultipleChoiceFilter(
        label='Region', queryset=Region.objects.all(), widget=filters.widgets.CSVWidget, method='filter_regions')
    operation_type = filters.MultipleChoiceFilter(choices=OperationTypes.choices(), widget=filters.widgets.CSVWidget)
    programme_type = filters.MultipleChoiceFilter(choices=ProgrammeTypes.choices(), widget=filters.widgets.CSVWidget)
    primary_sector = filters.MultipleChoiceFilter(choices=Sectors.choices(), widget=filters.widgets.CSVWidget)
    secondary_sectors = filters.MultipleChoiceFilter(
        choices=SectorTags.choices(), widget=filters.widgets.CSVWidget, method='filter_secondary_sectors',
    )
    status = filters.MultipleChoiceFilter(choices=Statuses.choices(), widget=filters.widgets.CSVWidget)

    # Supporting/Receiving NS Filters (Multiselect)
    project_country = filters.ModelMultipleChoiceFilter(queryset=Country.objects.all(), widget=filters.widgets.CSVWidget)
    reporting_ns = filters.ModelMultipleChoiceFilter(queryset=Country.objects.all(), widget=filters.widgets.CSVWidget)

    def filter_secondary_sectors(self, queryset, name, value):
        if len(value):
            return queryset.filter(secondary_sectors__overlap=value)
        return queryset

    def filter_countries(self, queryset, name, countries):
        countries = countries.split(',')
        if len(countries):
            return queryset.filter(
                reduce(
                    lambda acc, item: acc | item,
                    [
                        (
                            # ISO2
                            Q(project_country__iso__iexact=country) |
                            Q(project_districts__country__iso__iexact=country) |
                            # ISO3
                            Q(project_country__iso3__iexact=country) |
                            Q(project_districts__country__iso3__iexact=country)
                        )
                        for country in countries
                    ]
                )
            ).distinct()
        return queryset

    def filter_regions(self, queryset, name, regions):
        if len(regions):
            return queryset.filter(
                Q(project_country__region__in=regions) |
                Q(project_districts__country__region__in=regions)
            ).distinct()
        return queryset

    class Meta:
        model = Project
        fields = [
            'country',
            'budget_amount',
            'start_date',
            'end_date',
            'project_districts',
            'reporting_ns',
            'programme_type',
            'status',
            'primary_sector',
            'operation_type',
        ]
