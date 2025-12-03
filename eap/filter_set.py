import django_filters as filters

from api.models import Country, DisasterType
from eap.models import EAPRegistration, EAPStatus, EAPType, FullEAP, SimplifiedEAP


class BaseFilterSet(filters.FilterSet):
    created_at = filters.DateFilter(
        field_name="created_at",
        lookup_expr="exact",
        input_formats=["%Y-%m-%d"],
    )
    created_at__lte = filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
        input_formats=["%Y-%m-%d"],
    )
    created_at__gte = filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
        input_formats=["%Y-%m-%d"],
    )


class EAPRegistrationFilterSet(BaseFilterSet):
    eap_type = filters.ChoiceFilter(
        choices=EAPType.choices,
        label="EAP Type",
    )
    status = filters.ChoiceFilter(
        choices=EAPStatus.choices,
        label="EAP Status",
    )

    # Country
    country = filters.ModelMultipleChoiceFilter(
        field_name="country",
        queryset=Country.objects.all(),
    )
    national_society = filters.ModelMultipleChoiceFilter(
        field_name="national_society",
        queryset=Country.objects.all(),
    )
    region = filters.NumberFilter(
        field_name="country__region_id",
        label="Region",
    )
    partners = filters.ModelMultipleChoiceFilter(
        field_name="partners",
        queryset=Country.objects.all(),
    )

    # Disaster
    disaster_type = filters.ModelMultipleChoiceFilter(
        field_name="disaster_type",
        queryset=DisasterType.objects.all(),
    )

    class Meta:
        model = EAPRegistration
        fields = ()


class BaseEAPFilterSet(BaseFilterSet):
    eap_registration = filters.ModelMultipleChoiceFilter(
        field_name="eap_registration",
        queryset=EAPRegistration.objects.all(),
    )

    seap_timeframe = filters.NumberFilter(
        field_name="seap_timeframe",
        label="SEAP Timeframe (in Years)",
    )

    national_society = filters.ModelMultipleChoiceFilter(
        field_name="eap_registration__national_society",
        queryset=Country.objects.all(),
    )

    country = filters.ModelMultipleChoiceFilter(
        field_name="eap_registration__country",
        queryset=Country.objects.all(),
    )

    disaster_type = filters.ModelMultipleChoiceFilter(
        field_name="eap_registration__disaster_type",
        queryset=DisasterType.objects.all(),
    )


class SimplifiedEAPFilterSet(BaseEAPFilterSet, BaseFilterSet):
    class Meta:
        model = SimplifiedEAP
        fields = ("eap_registration",)


class FullEAPFilterSet(BaseEAPFilterSet):
    class Meta:
        model = FullEAP
        fields = ("eap_registration",)
