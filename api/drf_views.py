from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import (
    Avg,
    Case,
    Count,
    ExpressionWrapper,
    F,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    When,
)
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce, TruncMonth
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as rest_filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filter_set import (
    Admin2Filter,
    AppealDocumentFilter,
    AppealHistoryFilter,
    CountryFilter,
    CountryFilterRMD,
    CountryKeyDocumentFilter,
    CountryKeyFigureFilter,
    CountrySnippetFilter,
    CountrySupportingPartnerFilter,
    DistrictFilter,
    DistrictRMDFilter,
    EventFilter,
    EventSeverityLevelHistoryFilter,
    EventSnippetFilter,
    FieldReportFilter,
    GoHistoricalFilter,
    RegionKeyFigureFilter,
    RegionSnippetFilter,
    SituationReportFilter,
    UserFilterSet,
)
from api.visibility_class import (
    ReadOnlyVisibilityViewset,
    ReadOnlyVisibilityViewsetMixin,
)
from country_plan.models import CountryPlan
from databank.serializers import CountryOverviewSerializer
from deployments.models import ERU, Personnel
from deployments.serializers import ListDeployedERUByEventSerializer
from main.enums import GlobalEnumSerializer, get_enum_values
from main.filters import NullsLastOrderingFilter
from main.permissions import DenyGuestUserMutationPermission, DenyGuestUserPermission
from main.utils import is_tableau
from per.models import Overview
from per.serializers import CountryLatestOverviewSerializer

from .exceptions import BadRequest
from .models import (
    Action,
    Admin2,
    Appeal,
    AppealDocument,
    AppealHistory,
    AppealType,
    Country,
    CountryKeyDocument,
    CountryKeyFigure,
    CountryOfFieldReportToReview,
    CountrySnippet,
    CountrySupportingPartner,
    DisasterType,
    District,
    Event,
    EventFeaturedDocument,
    EventSeverityLevelHistory,
    Export,
    ExternalPartner,
    FieldReport,
    MainContact,
    Profile,
    Region,
    RegionKeyFigure,
    RegionSnippet,
    SituationReport,
    SituationReportType,
    Snippet,
    SupportedActivity,
    UserCountry,
    VisibilityChoices,
)
from .serializers import (  # AppealSerializer,; Tableau Serializers; AppealTableauSerializer,; Go Historical
    ActionSerializer,
    Admin2Serializer,
    AppealDocumentSerializer,
    AppealDocumentTableauSerializer,
    AppealHistorySerializer,
    AppealHistoryTableauSerializer,
    CountryDisasterTypeCountSerializer,
    CountryDisasterTypeMonthlySerializer,
    CountryGeoSerializer,
    CountryKeyDocumentSerializer,
    CountryKeyFigureInputSerializer,
    CountryKeyFigureSerializer,
    CountryOfFieldReportToReviewSerializer,
    CountryRelationSerializer,
    CountrySerializerRMD,
    CountrySnippetSerializer,
    CountrySnippetTableauSerializer,
    CountrySupportingPartnerSerializer,
    CountryTableauSerializer,
    DeploymentsByEventSerializer,
    DetailEventSerializer,
    DisasterTypeSerializer,
    DistrictSerializer,
    DistrictSerializerRMD,
    EventSeverityLevelHistorySerializer,
    ExportSerializer,
    ExternalPartnerSerializer,
    FieldReportGeneratedTitleSerializer,
    FieldReportGenerateTitleSerializer,
    FieldReportSerializer,
    GoHistoricalSerializer,
    HistoricalDisasterSerializer,
    ListEventCsvSerializer,
    ListEventDeploymentsSerializer,
    ListEventSerializer,
    ListEventTableauSerializer,
    ListFieldReportCsvSerializer,
    ListFieldReportTableauSerializer,
    ListMiniEventSerializer,
    MainContactSerializer,
    MiniCountrySerializer,
    MiniDistrictGeoSerializer,
    NsSerializer,
    ProfileSerializer,
    RegionGeoSerializer,
    RegionKeyFigureSerializer,
    RegionRelationSerializer,
    RegionSnippetSerializer,
    RegionSnippetTableauSerializer,
    SituationReportSerializer,
    SituationReportTableauSerializer,
    SituationReportTypeSerializer,
    SnippetSerializer,
    SupportedActivitySerializer,
    UserMeSerializer,
    UserSerializer,
)
from .utils import generate_field_report_title, is_user_ifrc


class DeploymentsByEventViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeploymentsByEventSerializer

    def get_queryset(self):
        today = timezone.now().date().strftime("%Y-%m-%d")
        active_personnel_prefetch = models.Prefetch(
            "personneldeployment_set__personnel_set",
            queryset=(
                Personnel.objects.filter(
                    type=Personnel.TypeChoices.RR,
                    start_date__date__lte=today,
                    end_date__date__gte=today,
                    is_active=True,
                ).select_related("country_from")
            ),
        )
        return (
            Event.objects.filter(
                personneldeployment__isnull=False,
                personneldeployment__personnel__type=Personnel.TypeChoices.RR,
                personneldeployment__personnel__is_active=True,
                personneldeployment__personnel__start_date__date__lte=today,
                personneldeployment__personnel__end_date__date__gte=today,
            )
            .prefetch_related(
                active_personnel_prefetch,
                "personneldeployment_set__country_deployed_to",
                "appeals",
            )
            .order_by(
                "-disaster_start_date",
            )
            .distinct()
        )


# These two should give the same result: ^ v
class EventDeploymentsViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListEventDeploymentsSerializer

    def get_queryset(self):
        today = timezone.now().date().strftime("%Y-%m-%d")
        return (
            Personnel.objects.filter(start_date__date__lte=today, end_date__date__gte=today, is_active=True)
            .order_by()
            .values(
                "deployment__event_deployed_to",
                "type",
            )
            .annotate(id=models.F("deployment__event_deployed_to"), deployments=models.Count("type"))
            .values("id", "type", "deployments")
        )


class EventSeverityLevelHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventSeverityLevelHistory.objects.select_related("event", "created_by").order_by("-created_at")
    serializer_class = EventSeverityLevelHistorySerializer
    filter_class = EventSeverityLevelHistoryFilter


class DeployedERUFilter(rest_filters.FilterSet):
    eru_type = rest_filters.NumberFilter(field_name="eru__type", lookup_expr="exact")


class DeployedERUByEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListDeployedERUByEventSerializer
    filterset_class = DeployedERUFilter

    def get_queryset(self):
        today = timezone.now().date().strftime("%Y-%m-%d")
        active_eru_prefetch = models.Prefetch(
            "eru_set",
            queryset=(
                ERU.objects.filter(
                    deployed_to__isnull=False,
                    start_date__date__lte=today,
                    end_date__date__gte=today,
                ).select_related(
                    "eru_owner__national_society_country",
                )
            ),
        )
        return (
            Event.objects.filter(
                eru__deployed_to__isnull=False,
                eru__start_date__date__lte=today,
                eru__end_date__date__gte=today,
            )
            .prefetch_related(
                active_eru_prefetch,
                "appeals",
            )
            .order_by(
                "-disaster_start_date",
            )
            .distinct()
        )


class DisasterTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DisasterType.objects.all()
    serializer_class = DisasterTypeSerializer
    search_fields = ("name",)  # for /docs


class RegionViewset(viewsets.ReadOnlyModelViewSet):
    """Region endpoint with snippet visibility filtering."""

    queryset = Region.objects.annotate(
        country_plan_count=Count("country__country_plan", filter=Q(country__country_plan__is_publish=True))
    )

    def get_queryset(self):
        """Apply snippet visibility filtering at the queryset level.

        This removes the need for serializer-side filtering. Rules:
        - Anonymous / guest: only PUBLIC
        - IFRC user: all visibilities
        - Auth non-IFRC: exclude IFRC; include IFRC_NS only if user has a country whose region matches the snippet's region.
        - MEMBERSHIP available to any authenticated non-guest user (already covered by exclude-only logic)

        We implement the IFRC_NS conditional by computing the set of region IDs the user is linked to via UserCountry/Profile
        and excluding IFRC_NS snippets for regions not in that set.
        """
        from .models import (
            Country,
            Profile,
            RegionSnippet,
            UserCountry,
            VisibilityChoices,
        )
        from .utils import is_user_ifrc

        user = getattr(self.request, "user", None)

        if not user or not user.is_authenticated:
            # Guests: only PUBLIC and exclude backend-gated power_bi embeds entirely
            snip_qs = RegionSnippet.objects.filter(visibility=VisibilityChoices.PUBLIC).exclude(
                snippet__contains='data-snippet-type="power_bi"'
            )
        else:
            profile = getattr(user, "profile", None)
            if profile and profile.limit_access_to_guest:
                snip_qs = RegionSnippet.objects.filter(visibility=VisibilityChoices.PUBLIC).exclude(
                    snippet__contains='data-snippet-type="power_bi"'
                )
            elif is_user_ifrc(user):
                snip_qs = RegionSnippet.objects.all()
            else:
                # User-linked countries (Profile.country is optional)
                user_country_ids = UserCountry.objects.filter(user=user.id).values_list("country", flat=True)
                profile_country_ids = Profile.objects.filter(user=user.id).values_list("country", flat=True)
                combined_country_ids = list(user_country_ids.union(profile_country_ids))
                # Regions the user is associated with via countries
                allowed_region_ids_for_ifrc_ns = Country.objects.filter(
                    id__in=combined_country_ids, region__isnull=False
                ).values_list("region_id", flat=True)
                snip_qs = RegionSnippet.objects.exclude(visibility=VisibilityChoices.IFRC)
                # Exclude IFRC_NS snippets whose region not in allowed set
                snip_qs = snip_qs.exclude(
                    Q(visibility=VisibilityChoices.IFRC_NS) & ~Q(region_id__in=allowed_region_ids_for_ifrc_ns)
                )
                # Exclude power_bi embedded snippets if marked auth-required and user is not IFRC
                snip_qs = snip_qs.exclude(snippet__contains='data-snippet-type="power_bi"')

        return self.queryset.prefetch_related(models.Prefetch("snippets", queryset=snip_qs))

    def get_serializer_class(self):
        if self.action == "list":
            return RegionGeoSerializer
        return RegionRelationSerializer


class CountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.filter(is_deprecated=False).annotate(
        has_country_plan=models.Exists(CountryPlan.objects.filter(country=OuterRef("pk"), is_publish=True))
    )
    filterset_class = CountryFilter
    ordering_fields = "__all__"
    search_fields = ("name",)  # for /docs

    def get_object(self):
        # NOTE: kwargs is accepting pk for now
        # TODO: Can kwargs be other than pk??
        pk = self.kwargs["pk"]
        try:
            country = get_object_or_404(Country, pk=int(pk))
            return self.get_queryset().filter(id=country.id).first()
        except ValueError:
            raise Exception("An error occured", "Country key is unusable", pk)

    def get_serializer_class(self):
        if self.request.GET.get("mini", "false").lower() == "true":
            return MiniCountrySerializer
        if is_tableau(self.request) is True:
            return CountryTableauSerializer
        if self.action == "list":
            return CountryGeoSerializer
        return CountryRelationSerializer

    @extend_schema(
        request=None,
        responses=CountryOverviewSerializer,
    )
    @action(
        detail=True,
        url_path="databank",
        # Only for Documentation
        serializer_class=CountryOverviewSerializer,
        pagination_class=None,
    )
    def get_databank(self, request, pk):
        country = self.get_object()
        if hasattr(country, "countryoverview"):
            return Response(CountryOverviewSerializer(country.countryoverview).data)
        raise Http404

    # Country property
    @extend_schema(
        request=None,
        parameters=[CountryKeyFigureInputSerializer],
        responses=CountryKeyFigureSerializer,
    )
    @action(
        detail=True,
        url_path="figure",
    )
    def get_country_figure(self, request, pk):
        country = self.get_object()

        now = timezone.now()
        start_date_from = request.GET.get("start_date_from", timezone.now() + timedelta(days=-2 * 365))
        start_date_to = request.GET.get("start_date_to", timezone.now())

        appeal_conditions = Q(atype=AppealType.APPEAL) | Q(atype=AppealType.INTL)

        all_appealhistory = AppealHistory.objects.select_related("appeal").filter(
            country=country,
            appeal__code__isnull=False,
            valid_from__lt=now,  # TODO: Allow user to provide this?
            valid_to__gt=now,  # TODO: Allow user to provide this?
        )
        if start_date_from and start_date_to:
            all_appealhistory = all_appealhistory.filter(
                start_date__gte=start_date_from,
                start_date__lte=start_date_to,
            )

        appeals_aggregated = all_appealhistory.annotate(
            appeal_with_dref=Count(
                Case(
                    When(Q(atype=AppealType.DREF), then=1),
                    output_field=IntegerField(),
                )
            ),
            appeal_without_dref=Count(Case(When(appeal_conditions, then=1), output_field=IntegerField())),
            total_population=(
                Case(
                    When(appeal_conditions | Q(atype=AppealType.DREF), then=F("num_beneficiaries")),
                    output_field=IntegerField(),
                )
            ),
            amount_requested_all=(
                Case(
                    When(appeal_conditions, then=F("amount_requested")),
                    output_field=IntegerField(),
                )
            ),
            amordref=(
                Case(
                    When(appeal_conditions | Q(atype=AppealType.DREF), then=F("amount_requested")),
                    output_field=IntegerField(),
                )
            ),
            amof=(
                Case(
                    When(appeal_conditions, then=F("amount_funded")),
                    output_field=IntegerField(),
                )
            ),
            amofdref=(
                Case(
                    When(appeal_conditions | Q(atype=AppealType.DREF), then=F("amount_funded")),
                    output_field=IntegerField(),
                )
            ),
            emergencies_count=Count(F("appeal__event_id"), distinct=True),
        ).aggregate(
            active_drefs=Sum("appeal_with_dref"),
            active_appeals=Sum("appeal_without_dref"),
            target_population=Sum("total_population"),
            amount_requested=Sum("amount_requested_all"),
            amount_requested_dref_included=Sum("amordref"),
            amount_funded=Sum("amof"),
            amount_funded_dref_included=Sum("amofdref"),
            emergencies=Sum("emergencies_count"),
        )
        return Response(CountryKeyFigureSerializer(appeals_aggregated).data)

    @extend_schema(
        request=None,
        parameters=[CountryKeyFigureInputSerializer],
        methods=["GET"],
        responses=CountryDisasterTypeCountSerializer(many=True),
    )
    @action(detail=True, url_path="disaster-count", pagination_class=None)
    def get_country_disaster_count(self, request, pk):
        country = self.get_object()

        start_date_from = request.GET.get("start_date_from", timezone.now() + timedelta(days=-2 * 365))
        start_date_to = request.GET.get("start_date_to", timezone.now())

        queryset = (
            Event.objects.filter(
                countries__in=[country.id],
                dtype__isnull=False,
            )
            .values("countries", "dtype__name")
            .annotate(
                count=Count("id"),
                disaster_name=F("dtype__name"),
                disaster_id=F("dtype__id"),
            )
            .order_by("countries", "dtype__name")
        )

        if start_date_from and start_date_to:
            queryset = queryset.filter(
                disaster_start_date__gte=start_date_from,
                disaster_start_date__lte=start_date_to,
            )

        return Response(CountryDisasterTypeCountSerializer(queryset, many=True).data)

    @extend_schema(
        request=None,
        parameters=[CountryKeyFigureInputSerializer],
        responses=CountryDisasterTypeMonthlySerializer(many=True),
    )
    @action(detail=True, url_path="disaster-monthly-count", pagination_class=None)
    def get_country_disaster_monthly_count(self, request, pk):
        country = self.get_object()

        start_date_from = request.GET.get("start_date_from", timezone.now() + timedelta(days=-2 * 365))
        start_date_to = request.GET.get("start_date_to", timezone.now())

        queryset = (
            Event.objects.filter(
                countries__in=[country.id],
                dtype__isnull=False,
            )
            .annotate(date=TruncMonth("disaster_start_date"))
            .values("date", "countries", "dtype")
            .annotate(
                appeal_targeted_population=Coalesce(
                    Avg(
                        "appeals__num_beneficiaries",
                        filter=models.Q(appeals__num_beneficiaries__isnull=False),
                        output_field=models.IntegerField(),
                    ),
                    0,
                ),
                latest_field_report_affected=Coalesce(
                    Subquery(
                        FieldReport.objects.filter(event=OuterRef("pk"))
                        .order_by()
                        .values("event")
                        .annotate(c=models.F("num_affected"))
                        .values("c")[:1],
                        output_field=models.IntegerField(),
                    ),
                    0,
                ),
                disaster_name=F("dtype__name"),
                disaster_id=F("dtype__id"),
            )
            .annotate(
                targeted_population=ExpressionWrapper(
                    (F("appeal_targeted_population") + F("latest_field_report_affected")), output_field=models.IntegerField()
                )
            )
            .order_by("date", "countries", "dtype__name")
        )

        if start_date_from and start_date_to:
            queryset = queryset.filter(
                disaster_start_date__gte=start_date_from,
                disaster_start_date__lte=start_date_to,
            )

        return Response(CountryDisasterTypeMonthlySerializer(queryset, many=True).data)

    @extend_schema(
        request=None,
        parameters=[CountryKeyFigureInputSerializer],
        responses=HistoricalDisasterSerializer(many=True),
    )
    @action(detail=True, url_path="historical-disaster", pagination_class=None)
    def get_country_historical_disaster(self, request, pk):
        country = self.get_object()

        start_date_from = request.GET.get("start_date_from", timezone.now() + timedelta(days=-2 * 365))
        start_date_to = request.GET.get("start_date_to", timezone.now())

        dtype = request.GET.get("dtype", None)

        queryset = (
            Event.objects.filter(
                countries__in=[country.id],
                dtype__isnull=False,
            )
            .annotate(date=TruncMonth("disaster_start_date"))
            .values("date", "dtype", "countries")
            .annotate(
                appeal_targeted_population=Coalesce(
                    Avg(
                        "appeals__num_beneficiaries",
                        filter=models.Q(appeals__num_beneficiaries__isnull=False),
                        output_field=models.IntegerField(),
                    ),
                    0,
                ),
                latest_field_report_affected=Coalesce(
                    Subquery(
                        FieldReport.objects.filter(event=OuterRef("pk"))
                        .order_by()
                        .values("event")
                        .annotate(c=models.F("num_affected"))
                        .values("c")[:1],
                        output_field=models.IntegerField(),
                    ),
                    0,
                ),
                disaster_name=F("dtype__name"),
                disaster_id=F("dtype__id"),
                amount_funded=F("appeals__amount_funded"),
                amount_requested=F("appeals__amount_requested"),
            )
            .annotate(
                targeted_population=ExpressionWrapper(
                    (F("appeal_targeted_population") + F("latest_field_report_affected")), output_field=models.IntegerField()
                )
            )
            .order_by("date", "countries", "dtype__name")
        )

        if start_date_from and start_date_to:
            queryset = queryset.filter(
                disaster_start_date__gte=start_date_from,
                disaster_start_date__lte=start_date_to,
            )

        if dtype:
            queryset = queryset.filter(dtype=dtype)

        return Response(HistoricalDisasterSerializer(queryset, many=True).data)

    @extend_schema(request=None, responses=CountryLatestOverviewSerializer)
    @action(detail=True, url_path="latest-per-overview", serializer_class=CountryLatestOverviewSerializer, pagination_class=None)
    def get_latest_per_overview(self, request, pk):
        country = self.get_object()
        queryset = (
            Overview.objects.filter(country_id=country.id)
            .select_related("country", "type_of_assessment")
            .order_by("-created_at")
            .first()
        )
        return Response(CountryLatestOverviewSerializer(queryset).data)


class CountryRMDViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.filter(is_deprecated=False).filter(iso3__isnull=False).exclude(iso3="")
    filterset_class = CountryFilterRMD
    search_fields = ("name",)
    serializer_class = CountrySerializerRMD


class CountryKeyDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CountryKeyDocument.objects.select_related("country")
    serializer_class = CountryKeyDocumentSerializer
    search_fields = ("name",)
    ordering_fields = (
        "year",
        "end_year",
    )
    # permission_classes = (IsAuthenticated,)
    filterset_class = CountryKeyDocumentFilter
    filter_backends = (NullsLastOrderingFilter, rest_filters.DjangoFilterBackend, filters.SearchFilter)


class DistrictRMDViewset(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.select_related("country").filter(is_deprecated=False)
    filterset_class = DistrictRMDFilter
    search_fields = (
        "name",
        "country__name",
    )
    serializer_class = DistrictSerializerRMD


class RegionKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionKeyFigureSerializer
    filterset_class = RegionKeyFigureFilter
    visibility_model_class = RegionKeyFigure


class CountryKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountryKeyFigureSerializer
    filterset_class = CountryKeyFigureFilter
    visibility_model_class = CountryKeyFigure


class RegionSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionSnippetSerializer
    filterset_class = RegionSnippetFilter
    visibility_model_class = RegionSnippet

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return RegionSnippetTableauSerializer
        return RegionSnippetSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated or (getattr(user, "profile", None) and user.profile.limit_access_to_guest):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        # Non-IFRC auth users: still exclude power_bi when present and auth_required
        if not is_user_ifrc(user):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        return qs


class CountrySnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountrySnippetSerializer
    filterset_class = CountrySnippetFilter
    visibility_model_class = CountrySnippet

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return CountrySnippetTableauSerializer
        return CountrySnippetSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated or (getattr(user, "profile", None) and user.profile.limit_access_to_guest):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        if not is_user_ifrc(user):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        return qs


class DistrictViewset(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.select_related("country").filter(country__is_deprecated=False).filter(is_deprecated=False)
    filterset_class = DistrictFilter
    search_fields = (
        "name",
        "country__name",
    )  # for /docs

    def get_serializer_class(self):
        if self.action == "list":
            return MiniDistrictGeoSerializer
        else:
            return DistrictSerializer


class Admin2Viewset(viewsets.ReadOnlyModelViewSet):
    filterset_class = Admin2Filter
    search_fields = ("name", "district__name", "district__country__name")
    serializer_class = Admin2Serializer

    def get_queryset(self):
        return (
            Admin2.objects.select_related("admin1")
            .filter(admin1__country__is_deprecated=False)
            .filter(admin1__is_deprecated=False)
            .filter(is_deprecated=False)
        )


class EventViewset(ReadOnlyVisibilityViewset):
    ordering_fields = (
        "disaster_start_date",
        "created_at",
        "dtype",
        "name",
        "summary",
        "num_affected",
        "glide",
        "ifrc_severity_level",
    )
    filterset_class = EventFilter
    visibility_model_class = Event
    search_fields = (
        "name",
        "countries__name",
        "dtype__name",
    )  # for /docs

    def get_queryset(self, *args, **kwargs):
        # import pdb; pdb.set_trace();
        today = timezone.now().date().strftime("%Y-%m-%d")
        qset = super().get_queryset()
        if self.action == "mini_events":
            # return Event.objects.filter(parent_event__isnull=True).select_related('dtype')
            return qset.filter(parent_event__isnull=True).select_related("dtype")
        if self.action == "response_activity_events":
            return (
                qset.filter(parent_event__isnull=True)
                .filter(Q(auto_generated=False) | Q(auto_generated_source="New field report"))
                .select_related("dtype")
            )
        return (
            # Event.objects.filter(parent_event__isnull=True)
            qset.filter(parent_event__isnull=True)
            .select_related("dtype")
            .prefetch_related(
                "regions",
                Prefetch("appeals", queryset=Appeal.objects.select_related("dtype", "event", "country", "region")),
                Prefetch("countries", queryset=Country.objects.select_related("region")),
                Prefetch("districts", queryset=District.objects.select_related("country")),
                Prefetch(
                    "field_reports",
                    queryset=FieldReport.objects.select_related("user", "dtype", "event").prefetch_related(
                        "districts", "countries", "regions", "contacts"
                    ),
                ),
                Prefetch("featured_documents", queryset=EventFeaturedDocument.objects.order_by("-id")),
            )
            .annotate(
                active_deployments=Count(
                    "personneldeployment__personnel",
                    filter=Q(
                        personneldeployment__personnel__type=Personnel.TypeChoices.RR,
                        personneldeployment__personnel__start_date__date__lte=today,
                        personneldeployment__personnel__end_date__date__gte=today,
                        personneldeployment__personnel__is_active=True,
                    ),
                )
            )
        )

    def get_serializer_class(self):
        if self.action == "mini_events":
            return ListMiniEventSerializer
        elif self.action == "list":
            request_format_type = self.request.GET.get("format", "json")
            if request_format_type == "csv":
                return ListEventCsvSerializer
            elif is_tableau(self.request) is True:
                return ListEventTableauSerializer
            else:
                return ListEventSerializer
        else:
            return DetailEventSerializer

    # Overwrite 'retrieve' because by default we filter to only non-merged Emergencies in 'get_queryset()'
    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            try:
                prefetches = [
                    "regions",
                    Prefetch("appeals", queryset=Appeal.objects.select_related("dtype", "event", "country", "region")),
                    Prefetch("countries", queryset=Country.objects.select_related("region")),
                    Prefetch("districts", queryset=District.objects.select_related("country")),
                    Prefetch("field_reports", queryset=FieldReport.objects.prefetch_related("countries", "contacts")),
                    Prefetch("featured_documents", queryset=EventFeaturedDocument.objects.order_by("-id")),
                ]
                if self.request.user.is_authenticated and not self.request.user.profile.limit_access_to_guest:
                    if is_user_ifrc(self.request.user):
                        instance = Event.objects.prefetch_related(*prefetches).get(pk=pk)
                    else:
                        user_countries = (
                            UserCountry.objects.filter(user=request.user.id)
                            .values("country")
                            .union(Profile.objects.filter(user=request.user.id).values("country"))
                        )
                        instance = (
                            Event.objects.prefetch_related(*prefetches)
                            .exclude(visibility=VisibilityChoices.IFRC)
                            .exclude(Q(visibility=VisibilityChoices.IFRC_NS) & ~Q(countries__id__in=user_countries))
                            .get(pk=pk)
                        )
                else:
                    instance = Event.objects.prefetch_related(*prefetches).filter(visibility=VisibilityChoices.PUBLIC).get(pk=pk)
                # instance = Event.get_for(request.user).get(pk=pk)
            except Exception:
                raise Http404
        elif kwargs["slug"]:
            instance = Event.objects.filter(slug=kwargs["slug"]).first()
            # instance = Event.get_for(request.user).filter(slug=kwargs['slug']).first()
            if not instance:
                raise Http404
        else:
            raise BadRequest("Emergency ID or Slug parameters are missing")

        serializer = self.get_serializer(instance)

        # Hide the "affected" values that are kept only for history – see (¤) in other code parts
        if "field_reports" in serializer.data:
            for j, fr in enumerate(serializer.data["field_reports"]):
                if "recent_affected" in fr:  # should always be True
                    for i, field in enumerate(
                        [
                            "num_affected",
                            "gov_num_affected",
                            "other_num_affected",
                            "num_potentially_affected",
                            "gov_num_potentially_affected",
                            "other_num_potentially_affected",
                        ]
                    ):
                        if fr["recent_affected"] - 1 != i and field in serializer.data["field_reports"][j]:
                            del serializer.data["field_reports"][j][field]
                    del serializer.data["field_reports"][j]["recent_affected"]
        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=ListMiniEventSerializer(many=True),
    )
    @action(methods=["get"], detail=False, url_path="mini")
    def mini_events(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ListMiniEventSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=ListEventSerializer(many=True),
    )
    @action(methods=["get"], detail=False, url_path="response-activity")
    def response_activity_events(self, request):
        return super().list(request)


class EventSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = SnippetSerializer
    filterset_class = EventSnippetFilter
    visibility_model_class = Snippet
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated or (getattr(user, "profile", None) and user.profile.limit_access_to_guest):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        if not is_user_ifrc(user):
            return qs.exclude(snippet__contains='data-snippet-type="power_bi"')
        return qs


class SituationReportTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReportType.objects.all()
    serializer_class = SituationReportTypeSerializer
    ordering_fields = ("type",)
    search_fields = ("type",)  # for /docs


class SituationReportViewset(ReadOnlyVisibilityViewsetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = SituationReport.objects.select_related("type").order_by("-is_pinned", "-created_at")
    authentication_classes = (TokenAuthentication,)
    serializer_class = SituationReportSerializer
    ordering_fields = (
        "created_at",
        "is_pinned",
        "name",
    )
    filterset_class = SituationReportFilter
    visibility_model_class = SituationReport
    search_fields = (
        "name",
        "event__name",
    )  # for /docs

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return SituationReportTableauSerializer
        return SituationReportSerializer


# Instead of viewsets.ReadOnlyModelViewSet:
class AppealViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Used to get Appeals from AppealHistory. Has no 'read' option, just 'list'."""

    queryset = AppealHistory.objects.select_related(
        "appeal__event",
        "dtype",
        "country",
        "region",
    ).filter(appeal__code__isnull=False)
    serializer_class = AppealHistorySerializer
    ordering_fields = "__all__"
    filterset_class = AppealHistoryFilter
    search_fields = (
        "appeal__name",
        "code",
    )  # for /docs

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return AppealHistoryTableauSerializer
        return AppealHistorySerializer

    def remove_unconfirmed_event(self, obj):
        if obj["needs_confirmation"]:
            obj["event"] = None
        return obj

    def remove_unconfirmed_events(self, objs):
        return [self.remove_unconfirmed_event(obj) for obj in objs]

    # Overwrite to exclude the events which require confirmation
    def list(self, request, *args, **kwargs):
        date = request.GET.get("date", timezone.now())
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                valid_from__lt=date,
                valid_to__gt=date,
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self.remove_unconfirmed_events(serializer.data))

        serializer = self.get_serializer(queryset, many=True)
        return Response(self.remove_unconfirmed_events(serializer.data))


#    def retrieve(self, request, *args, **kwargs):
#        instance = self.get_object()
#
#        serializer = self.get_serializer(instance)
#        return Response(self.remove_unconfirmed_event(serializer.data))


class AppealDocumentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AppealDocument.objects.select_related(
        "type",
        "iso",
    ).prefetch_related(
        "appeal__event__countries_for_preview",
    )
    ordering_fields = (
        "created_at",
        "type",
        "name",
    )
    filterset_class = AppealDocumentFilter
    search_fields = ("name", "appeal__code", "appeal__name")  # for /docs

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return AppealDocumentTableauSerializer
        return AppealDocumentSerializer


class ProfileViewset(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, DenyGuestUserPermission)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class UserViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    @action(detail=False, url_path="me", serializer_class=UserMeSerializer, permission_classes=(IsAuthenticated,))
    def get_authenticated_user_info(self, request, *args, **kwargs):
        return Response(self.get_serializer_class()(request.user).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="accepted_license_terms",
    )
    def accepted_license_terms(self, request, *args, **kwargs):
        user = request.user
        if user.profile.accepted_montandon_license_terms is True:
            raise serializers.ValidationError("User has already accepted the license terms")
        user.profile.accepted_montandon_license_terms = True
        user.profile.save(update_fields=["accepted_montandon_license_terms"])
        return Response(self.get_serializer_class()(user).data)


@extend_schema_view(retrieve=extend_schema(request=None, responses=FieldReportSerializer))
class FieldReportViewset(ReadOnlyVisibilityViewsetMixin, viewsets.ModelViewSet):
    search_fields = (
        "countries__name",
        "regions__label",
        "summary",
    )  # for /docs
    ordering_fields = ("summary", "event", "dtype", "created_at", "updated_at")
    filterset_class = FieldReportFilter
    permission_classes = [DenyGuestUserMutationPermission]
    queryset = FieldReport.objects.select_related("dtype", "event").prefetch_related(
        "actions_taken",
        "actions_taken__actions",
        "contacts",
        "countries",
        "districts",
        # Unusable – in serializer: wired-in get_merged_items_by_fields():
        # "event__countries",
        "external_partners",
        "regions",
        "sources",
        "supported_activities",
    )

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return ListFieldReportTableauSerializer
        if self.action == "list":
            request_format_type = self.request.GET.get("format", "json")
            if request_format_type == "csv":
                return ListFieldReportCsvSerializer
            else:
                return FieldReportSerializer
        return FieldReportSerializer

    @extend_schema(
        request=FieldReportGenerateTitleSerializer,
        responses=FieldReportGeneratedTitleSerializer,
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="generate-title",
        permission_classes=[DenyGuestUserMutationPermission],
    )
    def generate_title(self, request):
        """
        Generate a title for a Field Report.
        """
        serializer = FieldReportGenerateTitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        countries = serializer.validated_data.get("countries")
        dtype = serializer.validated_data.get("dtype")
        event = serializer.validated_data.get("event")
        start_date = serializer.validated_data.get("start_date")
        title = serializer.validated_data.get("title")
        is_covid_report = serializer.validated_data.get("is_covid_report")
        id = serializer.validated_data.get("id")

        summary = generate_field_report_title(
            country=countries[0],
            dtype=dtype,
            event=event,
            start_date=start_date,
            title=title,
            is_covid_report=is_covid_report,
            id=id,
        )
        return Response(
            FieldReportGeneratedTitleSerializer(
                {
                    "title": summary,
                }
            ).data
        )


class ActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Action.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer


class ExternalPartnerViewset(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalPartner.objects.all()
    serializer_class = ExternalPartnerSerializer


class SupportedActivityViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SupportedActivity.objects.all()
    serializer_class = SupportedActivitySerializer


# class GenericFieldReportView(GenericAPIView):
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     queryset = FieldReport.objects.all()

#     def serialize(self, data, instance=None):
#         # Replace integer values for Int Enum types.
#         # Otherwise, validation will fail.
#         # This applies to visibility and request choices.
#         if data["visibility"] == 2 or data["visibility"] == "2":
#             data["visibility"] = VisibilityChoices.IFRC
#         elif data["visibility"] == 3 or data["visibility"] == "3":
#             data["visibility"] = VisibilityChoices.PUBLIC
#         elif data["visibility"] == 4 or data["visibility"] == "4":
#             data["visibility"] = VisibilityChoices.IFRC_NS
#         else:
#             data["visibility"] = VisibilityChoices.MEMBERSHIP

#         # Set RecentAffected according to the sent _affected key – see (¤) in other code parts
#         if "status" in data and data["status"] == FieldReport.Status.EW:  # Early Warning
#             if "num_potentially_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.RCRC_POTENTIALLY
#             elif "gov_num_potentially_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT_POTENTIALLY
#             elif "other_num_potentially_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.OTHER_POTENTIALLY
#         else:  # Event related
#             if "num_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.RCRC
#             elif "gov_num_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT
#             elif "other_num_affected" in data:
#                 data["recent_affected"] = FieldReport.RecentAffected.OTHER

#         # Handle EPI Figures' Source dropdown saving
#         if "epi_figures_source" in data:
#             if data["epi_figures_source"] == 0 or data["epi_figures_source"] == "0":
#                 data["epi_figures_source"] = EPISourceChoices.MINISTRY_OF_HEALTH
#             elif data["epi_figures_source"] == 1 or data["epi_figures_source"] == "1":
#                 data["epi_figures_source"] = EPISourceChoices.WHO
#             elif data["epi_figures_source"] == 2 or data["epi_figures_source"] == "2":
#                 data["epi_figures_source"] = EPISourceChoices.OTHER
#             else:
#                 data["epi_figures_source"] = None
#         else:
#             data["epi_figures_source"] = None

#         request_choices = [
#             "bulletin",
#             "dref",
#             "appeal",
#             "rdrt",
#             "fact",
#             "emergency_response_unit",
#             "imminent_dref",
#             "forecast_based_action",
#             "eru_base_camp",
#             "eru_basic_health_care",
#             "eru_it_telecom",
#             "eru_logistics",
#             "eru_deployment_hospital",
#             "eru_referral_hospital",
#             "eru_relief",
#             "eru_water_sanitation_15",
#             "eru_water_sanitation_40",
#             "eru_water_sanitation_20",
#         ]
#         for prop in request_choices:
#             if prop in data:
#                 if data[prop] == 1 or data[prop] == "1":
#                     data[prop] = RequestChoices.REQUESTED
#                 elif data[prop] == 2 or data[prop] == "2":
#                     data[prop] = RequestChoices.PLANNED
#                 elif data[prop] == 3 or data[prop] == "3":
#                     data[prop] = RequestChoices.COMPLETE
#                 else:
#                     data[prop] = RequestChoices.NO

#         if instance is not None:
#             serializer = CreateFieldReportSerializer(instance, data=data)
#         else:
#             serializer = CreateFieldReportSerializer(data=data)
#         return serializer

#     def map_foreign_key_relations(self, data):
#         # The request data object will come with a lot of relation mappings.
#         # For foreign key, we want to replace instance ID's with querysets.

#         # Query foreign key relations, these are attached on model save/update.
#         mappings = [
#             ("user", User),
#             ("dtype", DisasterType),
#             ("event", Event),
#         ]
#         for prop, model in mappings:
#             if prop in data and data[prop] is not None:
#                 try:
#                     data[prop] = model.objects.get(pk=data[prop])
#                 except Exception:
#                     raise BadRequest("Valid %s is required" % prop)
#             elif prop != "event":
#                 raise BadRequest("Valid %s is required" % prop)

#         return data

#     def map_many_to_many_relations(self, data):
#         # Query many-to-many mappings. These are removed from the data object,
#         # So they can be added later.
#         mappings = [
#             ("countries", Country),
#             ("regions", Region),
#             ("districts", District),
#         ]

#         locations = {}
#         for prop, model in mappings:
#             if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
#                 locations[prop] = list(data[prop])
#             if prop in data:
#                 del data[prop]

#         # Sources, actions, and contacts
#         mappings = [
#             ("actions_taken"),
#             ("contacts"),
#             ("sources"),
#         ]

#         meta = {}
#         for prop in mappings:
#             if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
#                 meta[prop] = list(data[prop])
#             if prop in data:
#                 del data[prop]

#         mappings = [("external_partners", ExternalPartner), ("supported_activities", SupportedActivity)]

#         partners = {}
#         for prop, model in mappings:
#             if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
#                 partners[prop] = list(data[prop])
#             if prop in data:
#                 del data[prop]

#         if "start_date" in data:
#             data["start_date"] = datetime.strptime(data["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=utc)
#         if "sit_fields_date" in data:
#             data["sit_fields_date"] = datetime.strptime(data["sit_fields_date"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(
#                 tzinfo=utc
#             )
#         return data, locations, meta, partners

#     def save_locations(self, instance, locations, is_update=False):
#         if is_update:
#             instance.districts.clear()
#             instance.countries.clear()
#             instance.regions.clear()
#         if "districts" in locations:
#             instance.districts.add(*locations["districts"])
#         if "countries" in locations:
#             instance.countries.add(*locations["countries"])
#             # Add countries in automatically, based on regions
#             countries = Country.objects.filter(pk__in=locations["countries"])
#             instance.regions.add(*[country.region for country in countries if (country.region is not None)])

#     def save_partners_activities(self, instance, locations, is_update=False):
#         if is_update:
#             instance.external_partners.clear()
#             instance.supported_activities.clear()
#         if "external_partners" in locations:
#             instance.external_partners.add(*locations["external_partners"])
#         if "supported_activities" in locations:
#             instance.supported_activities.add(*locations["supported_activities"])

#     def save_meta(self, fieldreport, meta, is_update=False):
#         if is_update:
#             ActionsTaken.objects.filter(field_report=fieldreport).delete()
#             FieldReportContact.objects.filter(field_report=fieldreport).delete()
#             Source.objects.filter(field_report=fieldreport).delete()

#         if "actions_taken" in meta:
#             for action_taken in meta["actions_taken"]:
#                 actions = action_taken["actions"]
#                 del action_taken["actions"]
#                 action_taken[TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME] = django_get_language()
#                 actions_taken = ActionsTaken.objects.create(field_report=fieldreport, **action_taken)
#                 CreateFieldReportSerializer.trigger_field_translation(actions_taken)
#                 actions_taken.actions.add(*actions)

#         if "contacts" in meta:
#             FieldReportContact.objects.bulk_create(
#                 [FieldReportContact(field_report=fieldreport, **fields) for fields in meta["contacts"]]
#             )

#         if "sources" in meta:
#             for source in meta["sources"]:
#                 stype, created = SourceType.objects.get_or_create(name=source["stype"])
#                 source["stype"] = stype
#             Source.objects.bulk_create([Source(field_report=fieldreport, **fields) for fields in meta["sources"]])


# class CreateFieldReport(CreateAPIView, GenericFieldReportView):
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     queryset = FieldReport.objects.all()
#     serializer_class = CreateFieldReportSerializer

#     def create_event(self, report):
#         event = Event.objects.create(
#             name=report.summary,
#             dtype=report.dtype,
#             summary=report.description or "",
#             disaster_start_date=report.start_date,
#             auto_generated=True,
#             auto_generated_source=SOURCES["new_report"],
#             visibility=report.visibility,
#             **{TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME: django_get_language()},
#         )
#         CreateFieldReportSerializer.trigger_field_translation(event)
#         report.event = event
#         report.save()
#         return event

#     def create(self, request, *args, **kwargs):
#         serializer = self.serialize(request.data)
#         if not serializer.is_valid():
#             try:
#                 logger.error("Create Field Report serializer errors: {}".format(serializer.errors))
#             except Exception:
#                 logger.error("Could not log create Field Report serializer errors")
#             raise BadRequest(serializer.errors)

#         data = self.map_foreign_key_relations(request.data)
#         data, locations, meta, partners = self.map_many_to_many_relations(data)

#         try:
#             # TODO: Use serializer to create fieldreport
#             data[TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME] = django_get_language()
#             fieldreport = FieldReport.objects.create(
#                 **data,
#             )
#             CreateFieldReportSerializer.trigger_field_translation(fieldreport)
#         except Exception as e:
#             try:
#                 err_msg = str(e)
#                 logger.error("Could not create Field Report.", exc_info=True)
#                 raise BadRequest("Could not create Field Report. Error: {}".format(err_msg))
#             except Exception:
#                 raise BadRequest("Could not create Field Report")

#         # ### Creating relations ###
#         # These are *not* handled in a transaction block.
#         # The data model for these is very permissive. We're more interested in the
#         # Numerical data being there than not.
#         errors = []
#         try:
#             self.save_locations(fieldreport, locations)
#             self.save_partners_activities(fieldreport, partners)
#         except Exception as e:
#             errors.append(e)

#         try:
#             self.save_meta(fieldreport, meta)
#         except Exception as e:
#             errors.append(e)

#         # If the report doesn't have an emergency attached, create one.
#         if fieldreport.event is None:
#             event = self.create_event(fieldreport)
#             try:
#                 self.save_locations(event, locations)
#             except Exception as e:
#                 errors.append(e)

#         if len(errors):
#             logger.error("%s errors creating new field reports" % len(errors))
#             for error in errors:
#                 logger.error(str(error)[:200])

#         return Response({"id": fieldreport.id}, status=HTTP_201_CREATED)


# class UpdateFieldReport(UpdateAPIView, GenericFieldReportView):
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     queryset = FieldReport.objects.all()
#     serializer_class = CreateFieldReportSerializer

#     def partial_update(self, request, *args, **kwargs):
#         self.update(request, *args, **kwargs)

#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.serialize(request.data, instance=instance)
#         if not serializer.is_valid():
#             raise BadRequest(serializer.errors)

#         data = self.map_foreign_key_relations(request.data)
#         data, locations, meta, partners = self.map_many_to_many_relations(data)

#         try:
#             serializer.save()
#         except Exception:
#             logger.error("Faild to update field report", exc_info=True)
#             raise BadRequest("Could not update field report")

#         errors = []
#         try:
#             self.save_locations(instance, locations, is_update=True)
#             self.save_partners_activities(instance, partners, is_update=True)
#         except Exception as e:
#             errors.append(e)

#         try:
#             self.save_meta(instance, meta, is_update=True)
#         except Exception as e:
#             errors.append(e)

#         if len(errors):
#             logger.error("%s errors creating new field reports" % len(errors))
#             for error in errors:
#                 logger.error(str(error)[:200])

#         return Response({"id": instance.id}, status=HTTP_200_OK)


class MainContactViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = MainContactSerializer
    queryset = MainContact.objects.order_by("extent")
    search_fields = ("name", "email")  # for /docs


class NSLinksViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = NsSerializer
    queryset = Country.objects.filter(url_ifrc__contains="/").order_by("url_ifrc")


class GoHistoricalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GoHistoricalSerializer
    filterset_class = GoHistoricalFilter

    def get_queryset(self):
        return Event.objects.filter(appeals__isnull=False).distinct()


class CountryOfFieldReportToReviewViewset(viewsets.ReadOnlyModelViewSet):
    queryset = CountryOfFieldReportToReview.objects.order_by("country")
    serializer_class = CountryOfFieldReportToReviewSerializer
    search_fields = ("country__name",)  # for /docs

    class Meta:
        model = CountryOfFieldReportToReview
        fields = "country_id"


class UsersViewset(viewsets.ReadOnlyModelViewSet):
    """
    List all active users
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]
    filterset_class = UserFilterSet

    def get_queryset(self):

        return (
            User.objects.select_related(
                "profile",
                "profile__country",
            )
            .prefetch_related("subscription")
            .annotate(
                is_ifrc_admin=models.Exists(
                    Group.objects.filter(
                        name__iexact="IFRC Admins",
                        user=OuterRef("pk"),
                    )
                )
            )
            .filter(is_active=True)
        )


class GlobalEnumView(APIView):
    """
    Provide a single endpoint to fetch enum metadata
    """

    @extend_schema(responses=GlobalEnumSerializer)
    def get(self, _):
        """
        Return a list of all enums.
        """
        return Response(get_enum_values())


class ExportViewSet(viewsets.ModelViewSet):
    serializer_class = ExportSerializer
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]

    def get_queryset(self):
        user = self.request.user
        return Export.objects.filter(requested_by=user).distinct()


class CountrySupportingPartnerViewSet(viewsets.ModelViewSet):
    serializer_class = CountrySupportingPartnerSerializer
    filterset_class = CountrySupportingPartnerFilter

    def get_queryset(self):
        return CountrySupportingPartner.objects.select_related("country")
