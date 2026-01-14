import django_filters as filters
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from api.event_sources import SOURCES
from api.models import (
    Admin2,
    Appeal,
    AppealDocument,
    AppealHistory,
    AppealType,
    Country,
    CountryKeyDocument,
    CountryKeyFigure,
    CountrySnippet,
    CountrySupportingPartner,
    DimAgreementLine,
    District,
    Event,
    EventSeverityLevelHistory,
    FieldReport,
    Region,
    RegionKeyFigure,
    RegionSnippet,
    SituationReport,
    Snippet,
)
from api.view_filters import ListFilter
from per.models import (
    OpsLearningCacheResponse,
    OpsLearningComponentCacheResponse,
    OpsLearningSectorCacheResponse,
)


class UserFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name="username", lookup_expr="icontains")
    email = filters.CharFilter(field_name="email", lookup_expr="icontains")

    class Meta:
        model = User
        fields = ()


class EventSeverityLevelHistoryFilter(filters.FilterSet):
    # NOTE: Adding this fixed N + 1 for some reason
    # Getting this issue: NO SCROLL CURSOR WITH HOLD FOR SELECT
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")

    class Meta:
        model = EventSeverityLevelHistory
        fields = {
            "id": ("exact", "in"),
            "event": ("exact", "in"),
        }


class CountryFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")
    record_type = filters.NumberFilter(field_name="record_type", lookup_expr="exact")
    is_independent = filters.BooleanFilter(field_name="independent", label="is_independent", lookup_expr="exact")
    is_deprecated = filters.BooleanFilter(field_name="is_deprecated", label="is_deprecated", lookup_expr="exact")
    is_nationalsociety = filters.BooleanFilter(label="is_nationalsociety", method="filter_national_society")

    class Meta:
        model = Country
        fields = {
            "id": ("exact", "in"),
            "region": ("exact", "in"),
            "record_type": ("exact", "in"),
        }

    def filter_national_society(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            (models.Q(independent=True) & models.Q(society_name__isnull=False))
            | ((models.Q(name__icontains="RC")) | models.Q(iso="BX"))
        )


class CountryFilterRMD(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = Country
        fields = {
            "id": ("exact", "in"),
            "region": ("exact", "in"),
            "record_type": ("exact", "in"),
        }


class CountryKeyDocumentFilter(filters.FilterSet):
    year__lte = filters.DateFilter(field_name="year", lookup_expr="lte", input_formats=["%Y-%m-%d"])
    year__gte = filters.DateFilter(field_name="year", lookup_expr="gte", input_formats=["%Y-%m-%d"])
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")
    document_type = filters.CharFilter(field_name="document_type", lookup_expr="exact")

    class Meta:
        model = CountryKeyDocument
        fields = ()


class DistrictRMDFilter(filters.FilterSet):
    class Meta:
        model = District
        fields = {
            "id": ("exact", "in"),
            "country": ("exact", "in"),
            "country__iso3": ("exact", "in"),
            "country__name": ("exact", "in"),
            "name": ("exact", "in"),
        }


class RegionKeyFigureFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = RegionKeyFigure
        fields = ["region"]


class CountryKeyFigureFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = CountryKeyFigure
        fields = ("country",)


class RegionSnippetFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = RegionSnippet
        fields = ("region",)


class CountrySnippetFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = CountrySnippet
        fields = ("country",)


class DistrictFilter(filters.FilterSet):
    class Meta:
        model = District
        fields = {
            "id": ("exact", "in"),
            "country": ("exact", "in"),
            "country__iso3": ("exact", "in"),
            "country__name": ("exact", "in"),
            "name": ("exact", "in"),
        }


class Admin2Filter(filters.FilterSet):
    class Meta:
        model = Admin2
        fields = {
            "id": ("exact", "in"),
            "admin1": ("exact", "in"),
            "admin1__country": ("exact", "in"),
            "admin1__country__iso3": ("exact", "in"),
            "name": ("exact", "in"),
        }


class EventFilter(filters.FilterSet):
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    appeal_type = filters.MultipleChoiceFilter(
        choices=AppealType.choices,
        field_name="appeals__atype",
        widget=filters.widgets.CSVWidget,
        lookup_expr="in",
    )
    is_featured = filters.BooleanFilter(field_name="is_featured")
    is_featured_region = filters.BooleanFilter(field_name="is_featured_region")
    countries__in = ListFilter(field_name="countries__id")
    regions__in = ListFilter(field_name="regions__id")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    auto_generated_source = filters.ChoiceFilter(
        label="Auto generated source choices",
        choices=[(v, v) for v in SOURCES.values()],
    )
    is_subscribed = filters.BooleanFilter(label="is_subscribed", method="get_is_subcribed_event")

    class Meta:
        model = Event
        fields = {
            "disaster_start_date": ("exact", "gt", "gte", "lt", "lte"),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }

    def get_is_subcribed_event(self, qs, name, value):
        user = self.request.user
        if value:
            return qs.filter(subscription__user=user).distinct()
        return qs


class EventSnippetFilter(filters.FilterSet):
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")

    class Meta:
        model = Snippet
        fields = ("event",)


class SituationReportFilter(filters.FilterSet):
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")
    type = filters.NumberFilter(field_name="type", lookup_expr="exact")

    class Meta:
        model = SituationReport
        fields = {
            "name": ("exact",),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class AppealFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name="atype", lookup_expr="exact")
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")
    code = filters.CharFilter(field_name="code", lookup_expr="exact")
    status = filters.NumberFilter(field_name="status", lookup_expr="exact")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    appeal_id = filters.NumberFilter(
        field_name="appeal_id", lookup_expr="exact", help_text="Use this (or code) for appeal identification."
    )
    district = filters.ModelMultipleChoiceFilter(
        field_name="country__district", queryset=District.objects.all(), label="district", method="get_country_district"
    )
    admin2 = filters.ModelMultipleChoiceFilter(
        field_name="country__district__admin2",
        queryset=Admin2.objects.all(),
        label="admin2",
        method="get_country_admin2",
    )

    class Meta:
        model = Appeal
        fields = {
            "start_date": ("exact", "gt", "gte", "lt", "lte"),
            "end_date": ("exact", "gt", "gte", "lt", "lte"),
            "real_data_update": ("exact", "gt", "gte", "lt", "lte"),
            "country__iso3": ("exact",),
        }

    def get_country_district(self, qs, name, value):
        if value:
            return qs.filter(country__district=value).distinct()
        return qs

    def get_country_admin2(self, qs, name, value):
        if value:
            return qs.filter(country__district__admin2=value).distinct()
        return qs


class AppealHistoryFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name="atype", lookup_expr="exact")
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())
    region = filters.ModelMultipleChoiceFilter(field_name="region", queryset=Region.objects.all())
    code = filters.CharFilter(field_name="code", lookup_expr="exact")
    status = filters.NumberFilter(field_name="status", lookup_expr="exact")
    # Do not use, misleading: id = filters.NumberFilter(field_name='id', lookup_expr='exact')
    appeal_id = filters.NumberFilter(
        field_name="appeal_id", lookup_expr="exact", help_text="Use this (or code) for appeal identification."
    )
    district = filters.ModelMultipleChoiceFilter(
        field_name="country__district", queryset=District.objects.all(), label="district", method="get_country_district"
    )
    admin2 = filters.ModelMultipleChoiceFilter(
        field_name="country__district__admin2",
        queryset=Admin2.objects.all(),
        label="admin2",
        method="get_country_admin2",
    )

    class Meta:
        model = AppealHistory
        fields = {
            "start_date": ("exact", "gt", "gte", "lt", "lte"),
            "end_date": ("exact", "gt", "gte", "lt", "lte"),
            "valid_from": ("exact", "gt", "gte", "lt", "lte"),
            "valid_to": ("exact", "gt", "gte", "lt", "lte"),
            "appeal__real_data_update": ("exact", "gt", "gte", "lt", "lte"),
            "country__iso3": ("exact",),
        }

    def get_country_district(self, qs, name, value):
        if value:
            return qs.filter(country__district=value).distinct()
        return qs

    def get_country_admin2(self, qs, name, value):
        if value:
            return qs.filter(country__district__admin2=value).distinct()
        return qs


class AppealDocumentFilter(filters.FilterSet):
    appeal = filters.ModelMultipleChoiceFilter(
        method="get_appeal_filter",
        widget=filters.widgets.CSVWidget,
        queryset=Appeal.objects.all(),
    )
    # NOTE: Filters are used to get documents of used ops learning
    insight_id = filters.NumberFilter(
        label="Base Insight id for source document",
        method="get_cache_base_document",
    )
    insight_sector_id = filters.NumberFilter(label="Sector insight id for source document", method="get_cache_sector_document")
    insight_component_id = filters.NumberFilter(
        label="Component insight id for source document",
        method="get_cache_component_document",
    )

    class Meta:
        model = AppealDocument
        fields = {
            "name": ("exact",),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }

    def get_appeal_filter(self, qs, name, value):
        if value:
            return qs.filter(appeal__in=value).distinct()
        return qs

    def get_cache_base_document(self, qs, name, value):
        if value and (ops_learning_cache_response := OpsLearningCacheResponse.objects.filter(id=value).first()):
            return qs.filter(id__in=ops_learning_cache_response.used_ops_learning.values_list("appeal_document_id", flat=True))
        return qs

    def get_cache_sector_document(self, qs, name, value):
        if value and (ops_learning_sector_cache_response := OpsLearningSectorCacheResponse.objects.filter(id=value).first()):
            return qs.filter(
                id__in=ops_learning_sector_cache_response.used_ops_learning.values_list("appeal_document_id", flat=True)
            )
        return qs

    def get_cache_component_document(self, qs, name, value):
        if value and (
            ops_learning_component_cache_response := OpsLearningComponentCacheResponse.objects.filter(id=value).first()
        ):
            return qs.filter(
                id__in=ops_learning_component_cache_response.used_ops_learning.values_list("appeal_document_id", flat=True)
            )
        return qs


class FieldReportFilter(filters.FilterSet):
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    user = filters.NumberFilter(field_name="user", lookup_expr="exact")
    countries__in = ListFilter(field_name="countries__id")
    regions__in = ListFilter(field_name="regions__id")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    is_covid_report = filters.BooleanFilter(field_name="is_covid_report")
    summary = filters.CharFilter(field_name="summary", lookup_expr="icontains")

    class Meta:
        model = FieldReport
        fields = {
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
            "updated_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class GoHistoricalFilter(filters.FilterSet):
    countries = filters.ModelMultipleChoiceFilter(field_name="countries", queryset=Country.objects.all())
    iso3 = filters.CharFilter(field_name="countries__iso3", lookup_expr="icontains")
    region = filters.NumberFilter(field_name="countries__region", lookup_expr="exact")

    class Meta:
        model = Event
        fields = ()


class CountrySupportingPartnerFilter(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())

    class Meta:
        model = CountrySupportingPartner
        fields = ()

class FabricDimAgreementLineFilter(filters.FilterSet):
    # Exact filters
    agreement_id = filters.CharFilter(field_name="agreement_id", lookup_expr="exact")
    agreement_line_id = filters.CharFilter(field_name="agreement_line_id", lookup_expr="exact")
    line_number = filters.NumberFilter(field_name="line_number", lookup_expr="exact")

    # Partial-match filters
    product = filters.CharFilter(field_name="product", lookup_expr="icontains")
    product_category = filters.CharFilter(field_name="product_category", lookup_expr="icontains")
    commitment_type = filters.CharFilter(field_name="commitment_type", lookup_expr="icontains")
    delivery_term = filters.CharFilter(field_name="delivery_term", lookup_expr="icontains")
    unit_of_measure = filters.CharFilter(field_name="unit_of_measure", lookup_expr="icontains")

    # Date range filters
    effective_date_after = filters.DateTimeFilter(field_name="effective_date", lookup_expr="gte")
    effective_date_before = filters.DateTimeFilter(field_name="effective_date", lookup_expr="lte")
    expiration_date_after = filters.DateTimeFilter(field_name="expiration_date", lookup_expr="gte")
    expiration_date_before = filters.DateTimeFilter(field_name="expiration_date", lookup_expr="lte")

    # Global search across multiple fields: ?q=term
    q = filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(agreement_line_id__icontains=value)
            | Q(agreement_id__icontains=value)
            | Q(product__icontains=value)
            | Q(product_category__icontains=value)
            | Q(commitment_type__icontains=value)
            | Q(delivery_term__icontains=value)
            | Q(unit_of_measure__icontains=value)
        )

    # Sorting: ?sort=field or ?sort=-field
    sort = filters.OrderingFilter(
        fields=(
            ("id", "id"),
            ("agreement_line_id", "agreement_line_id"),
            ("agreement_id", "agreement_id"),
            ("line_number", "line_number"),
            ("effective_date", "effective_date"),
            ("expiration_date", "expiration_date"),
            ("committed_quantity", "committed_quantity"),
            ("committed_amount", "committed_amount"),
            ("price_per_unit", "price_per_unit"),
            ("line_discount_percent", "line_discount_percent"),
        )
    )

    class Meta:
        model = DimAgreementLine
        fields = [
            "agreement_line_id",
            "agreement_id",
            "line_number",
            "product",
            "product_category",
            "commitment_type",
            "delivery_term",
            "unit_of_measure",
            "effective_date_after",
            "effective_date_before",
            "expiration_date_after",
            "expiration_date_before",
            "q",
            "sort",
        ]