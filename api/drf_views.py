from datetime import datetime
from pytz import utc
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from django.http import Http404
from django_filters import rest_framework as filters
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Prefetch, Count, Q, OuterRef
from django.utils import timezone
from django.utils.translation import get_language as django_get_language
from drf_spectacular.utils import extend_schema

from main.utils import is_tableau
from main.enums import GlobalEnumSerializer, get_enum_values
from main.translation import TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME
from deployments.models import Personnel
from databank.serializers import CountryOverviewSerializer

from .utils import is_user_ifrc
from .event_sources import SOURCES
from .exceptions import BadRequest
from .view_filters import ListFilter
from .visibility_class import ReadOnlyVisibilityViewset

from .models import (
    AppealHistory,
    DisasterType,
    ExternalPartner,
    SupportedActivity,
    Region,
    RegionKeyFigure,
    RegionSnippet,
    Country,
    CountryKeyFigure,
    CountrySnippet,
    District,
    Admin2,
    Event,
    Snippet,
    SituationReport,
    SituationReportType,
    Appeal,
    AppealDocument,
    Profile,
    FieldReport,
    FieldReportContact,
    Action,
    ActionsTaken,
    Source,
    SourceType,
    VisibilityChoices,
    RequestChoices,
    EPISourceChoices,
    MainContact,
    UserCountry,
    CountryOfFieldReportToReview,
)

from country_plan.models import CountryPlan

from .serializers import (
    ActionSerializer,
    DisasterTypeSerializer,
    ExternalPartnerSerializer,
    SupportedActivitySerializer,
    RegionGeoSerializer,
    RegionKeyFigureSerializer,
    RegionSnippetSerializer,
    RegionRelationSerializer,
    CountryGeoSerializer,
    MiniCountrySerializer,
    CountryKeyFigureSerializer,
    CountrySnippetSerializer,
    CountryRelationSerializer,
    CountrySerializerRMD,
    DistrictSerializer,
    MiniDistrictGeoSerializer,
    DistrictSerializerRMD,
    Admin2Serializer,
    SnippetSerializer,
    ListMiniEventSerializer,
    ListEventSerializer,
    ListEventCsvSerializer,
    ListEventDeploymentsSerializer,
    DeploymentsByEventSerializer,
    DetailEventSerializer,
    SituationReportSerializer,
    SituationReportTypeSerializer,
    # AppealSerializer,
    AppealHistorySerializer,
    AppealDocumentSerializer,
    UserSerializer,
    UserMeSerializer,
    ProfileSerializer,
    ListFieldReportSerializer,
    ListFieldReportCsvSerializer,
    DetailFieldReportSerializer,
    CreateFieldReportSerializer,
    MainContactSerializer,
    NsSerializer,
    # Tableau Serializers
    AppealDocumentTableauSerializer,
    # AppealTableauSerializer,
    AppealHistoryTableauSerializer,
    CountryTableauSerializer,
    CountrySnippetTableauSerializer,
    ListEventTableauSerializer,
    ListFieldReportTableauSerializer,
    RegionSnippetTableauSerializer,
    SituationReportTableauSerializer,
    # Go Historical
    GoHistoricalSerializer,
    CountryOfFieldReportToReviewSerializer,
)
from api.filter_set import UserFilterSet

from .logger import logger


class DeploymentsByEventViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeploymentsByEventSerializer

    def get_queryset(self):
        today = timezone.now().date().strftime("%Y-%m-%d")
        return (
            Event.objects.prefetch_related("personneldeployment_set__personnel_set__country_from")
            .annotate(
                personnel_count=Count(
                    "personneldeployment__personnel",
                    filter=Q(
                        personneldeployment__personnel__type=Personnel.TypeChoices.RR,
                        personneldeployment__personnel__start_date__date__lte=today,
                        personneldeployment__personnel__end_date__date__gte=today,
                        personneldeployment__personnel__is_active=True,
                    ),
                )
            )
            .filter(personnel_count__gt=0)
            .order_by("-disaster_start_date")
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


class DisasterTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DisasterType.objects.all()
    serializer_class = DisasterTypeSerializer
    search_fields = ("name",)  # for /docs


class RegionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.annotate(
        country_plan_count=Count("country__country_plan", filter=Q(country__country_plan__is_publish=True))
    )

    def get_serializer_class(self):
        if self.action == "list":
            return RegionGeoSerializer
        return RegionRelationSerializer


class CountryFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")
    record_type = filters.NumberFilter(field_name="record_type", lookup_expr="exact")

    class Meta:
        model = Country
        fields = {
            "id": ("exact", "in"),
            "region": ("exact", "in"),
            "record_type": ("exact", "in"),
        }


class CountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.filter(is_deprecated=False).annotate(
        has_country_plan=models.Exists(CountryPlan.objects.filter(country=OuterRef("pk"), is_publish=True))
    )
    filterset_class = CountryFilter
    search_fields = ("name",)  # for /docs

    def get_object(self):
        pk = self.kwargs["pk"]
        qs = self.get_queryset()
        try:
            return qs.get(pk=int(pk))
        except ValueError:
            # NOTE: If pk is not integer try searching for name or iso
            country = qs.filter(models.Q(name__iexact=str(pk)) | models.Q(iso__iexact=str(pk)))
            if country.exists():
                return country.first()
            raise Country.DoesNotExist("Country matching query does not exist.")

    def get_serializer_class(self):
        if self.request.GET.get("mini", "false").lower() == "true":
            return MiniCountrySerializer
        if is_tableau(self.request) is True:
            return CountryTableauSerializer
        if self.action == "list":
            return CountryGeoSerializer
        return CountryRelationSerializer

    @action(
        detail=True,
        url_path="databank",
        # Only for Documentation
        serializer_class=CountryOverviewSerializer,
    )
    def get_databank(self, request, pk):
        country = self.get_object()
        if hasattr(country, "countryoverview"):
            return Response(CountryOverviewSerializer(country.countryoverview).data)
        raise Http404


class CountryFilterRMD(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = Country
        fields = {
            "id": ("exact", "in"),
            "region": ("exact", "in"),
            "record_type": ("exact", "in"),
        }


class CountryRMDViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.filter(is_deprecated=False).filter(iso3__isnull=False).exclude(iso3="")
    filterset_class = CountryFilterRMD
    search_fields = ("name",)
    serializer_class = CountrySerializerRMD


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


class DistrictRMDViewset(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.select_related("country").filter(is_deprecated=False)
    filterset_class = DistrictRMDFilter
    search_fields = (
        "name",
        "country__name",
    )
    serializer_class = DistrictSerializerRMD


class RegionKeyFigureFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = RegionKeyFigure
        fields = ("region",)


class RegionKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionKeyFigureSerializer
    filterset_class = RegionKeyFigureFilter
    visibility_model_class = RegionKeyFigure


class CountryKeyFigureFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = CountryKeyFigure
        fields = ("country",)


class CountryKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountryKeyFigureSerializer
    filterset_class = CountryKeyFigureFilter
    visibility_model_class = CountryKeyFigure


class RegionSnippetFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")

    class Meta:
        model = RegionSnippet
        fields = ("region",)


class RegionSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionSnippetSerializer
    filterset_class = RegionSnippetFilter
    visibility_model_class = RegionSnippet

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return RegionSnippetTableauSerializer
        return RegionSnippetSerializer


class CountrySnippetFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = CountrySnippet
        fields = ("country",)


class CountrySnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountrySnippetSerializer
    filterset_class = CountrySnippetFilter
    visibility_model_class = CountrySnippet

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return CountrySnippetTableauSerializer
        return CountrySnippetSerializer


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


class EventFilter(filters.FilterSet):
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    is_featured = filters.BooleanFilter(field_name="is_featured")
    is_featured_region = filters.BooleanFilter(field_name="is_featured_region")
    countries__in = ListFilter(field_name="countries__id")
    regions__in = ListFilter(field_name="regions__id")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    auto_generated_source = filters.ChoiceFilter(
        label="Auto generated source choices",
        choices=[(v, v) for v in SOURCES.values()],
    )

    class Meta:
        model = Event
        fields = {
            "disaster_start_date": ("exact", "gt", "gte", "lt", "lte"),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class EventViewset(ReadOnlyVisibilityViewset):
    ordering_fields = (
        "disaster_start_date",
        "created_at",
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
                if self.request.user.is_authenticated:
                    if is_user_ifrc(self.request.user):
                        instance = Event.objects.get(pk=pk)
                    else:
                        user_countries = (
                            UserCountry.objects.filter(user=request.user.id)
                            .values("country")
                            .union(Profile.objects.filter(user=request.user.id).values("country"))
                        )
                        instance = (
                            Event.objects.exclude(visibility=VisibilityChoices.IFRC)
                            .exclude(Q(visibility=VisibilityChoices.IFRC_NS) & ~Q(countries__id__in=user_countries))
                            .get(pk=pk)
                        )
                else:
                    instance = Event.objects.filter(visibility=VisibilityChoices.PUBLIC).get(pk=pk)
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

    @action(methods=["get"], detail=False, url_path="mini")
    def mini_events(self, request):
        return super().list(request)

    @action(methods=["get"], detail=False, url_path="response-activity")
    def response_activity_events(self, request):
        return super().list(request)


class EventSnippetFilter(filters.FilterSet):
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")

    class Meta:
        model = Snippet
        fields = ("event",)


class EventSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = SnippetSerializer
    filterset_class = EventSnippetFilter
    visibility_model_class = Snippet


class SituationReportTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReportType.objects.all()
    serializer_class = SituationReportTypeSerializer
    ordering_fields = ("type",)
    search_fields = ("type",)  # for /docs


class SituationReportFilter(filters.FilterSet):
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")
    type = filters.NumberFilter(field_name="type", lookup_expr="exact")

    class Meta:
        model = SituationReport
        fields = {
            "name": ("exact",),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class SituationReportViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = SituationReportSerializer
    ordering_fields = (
        "created_at",
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


class AppealFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name="atype", lookup_expr="exact")
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")
    code = filters.CharFilter(field_name="code", lookup_expr="exact")
    status = filters.NumberFilter(field_name="status", lookup_expr="exact")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = Appeal
        fields = {
            "start_date": ("exact", "gt", "gte", "lt", "lte"),
            "end_date": ("exact", "gt", "gte", "lt", "lte"),
        }


class AppealHistoryFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name="atype", lookup_expr="exact")
    dtype = filters.NumberFilter(field_name="dtype", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")
    region = filters.NumberFilter(field_name="region", lookup_expr="exact")
    code = filters.CharFilter(field_name="code", lookup_expr="exact")
    status = filters.NumberFilter(field_name="status", lookup_expr="exact")
    # Do not use, misleading: id = filters.NumberFilter(field_name='id', lookup_expr='exact')
    appeal_id = filters.NumberFilter(
        field_name="appeal_id", lookup_expr="exact", help_text="Use this (or code) for appeal identification."
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


# Instead of viewsets.ReadOnlyModelViewSet:
class AppealViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Used to get Appeals from AppealHistory. Has no 'read' option, just 'list'."""

    # queryset = Appeal.objects.select_related('dtype', 'country', 'region').all()
    # queryset = AppealHistory.objects.select_related('appeal__event', 'dtype', 'country', 'region').all()
    queryset = AppealHistory.objects.select_related("appeal__event", "dtype", "country", "region").filter(
        appeal__code__isnull=False
    )
    # serializer_class = AppealSerializer
    serializer_class = AppealHistorySerializer
    ordering_fields = (
        "start_date",
        "end_date",
        "appeal__name",
        "aid",
        "dtype",
        "num_beneficiaries",
        "amount_requested",
        "amount_funded",
        "status",
        "atype",
        "event",
    )
    # filterset_class = AppealFilter
    filterset_class = AppealHistoryFilter
    search_fields = (
        "appeal__name",
        "code",
    )  # for /docs

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return AppealHistoryTableauSerializer
            # return AppealTableauSerializer
        return AppealHistorySerializer
        # return AppealSerializer

    def remove_unconfirmed_event(self, obj):
        if obj["needs_confirmation"]:
            obj["event"] = None
        return obj

    def remove_unconfirmed_events(self, objs):
        return [self.remove_unconfirmed_event(obj) for obj in objs]

    # Overwrite to exclude the events which require confirmation
    def list(self, request, *args, **kwargs):
        now = timezone.now()
        date = request.GET.get("date", now)
        queryset = self.filter_queryset(self.get_queryset()).filter(valid_from__lt=date, valid_to__gt=date)

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


class AppealDocumentFilter(filters.FilterSet):
    appeal = filters.NumberFilter(field_name="appeal", lookup_expr="exact")
    appeal__in = ListFilter(field_name="appeal__id")

    class Meta:
        model = AppealDocument
        fields = {
            "name": ("exact",),
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class AppealDocumentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AppealDocument.objects.all()
    ordering_fields = (
        "created_at",
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
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class UserViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    @action(
        detail=False,
        url_path="me",
        serializer_class=UserMeSerializer,
    )
    def get_authenticated_user_info(self, request, *args, **kwargs):
        return Response(self.get_serializer_class()(request.user).data)


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


class FieldReportViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    visibility_model_class = FieldReport
    search_fields = (
        "countries__name",
        "regions__label",
        "summary",
    )  # for /docs
    ordering_fields = ("summary", "event", "dtype", "created_at", "updated_at")
    filterset_class = FieldReportFilter

    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset()
            .select_related("dtype", "event")
            .prefetch_related("actions_taken", "actions_taken__actions", "countries", "districts", "regions")
        )

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return ListFieldReportTableauSerializer
        if self.action == "list":
            request_format_type = self.request.GET.get("format", "json")
            if request_format_type == "csv":
                return ListFieldReportCsvSerializer
            else:
                return ListFieldReportSerializer
        else:
            return DetailFieldReportSerializer


class ActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Action.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer


class ExternalPartnerViewset(viewsets.ReadOnlyModelViewSet):
    queryset = ExternalPartner.objects.all()
    serializer_class = ExternalPartnerSerializer


class SupportedActivityViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SupportedActivity.objects.all()
    serializer_class = SupportedActivitySerializer


class GenericFieldReportView(GenericAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()

    def serialize(self, data, instance=None):
        # Replace integer values for Int Enum types.
        # Otherwise, validation will fail.
        # This applies to visibility and request choices.
        if data["visibility"] == 2 or data["visibility"] == "2":
            data["visibility"] = VisibilityChoices.IFRC
        elif data["visibility"] == 3 or data["visibility"] == "3":
            data["visibility"] = VisibilityChoices.PUBLIC
        elif data["visibility"] == 4 or data["visibility"] == "4":
            data["visibility"] = VisibilityChoices.IFRC_NS
        else:
            data["visibility"] = VisibilityChoices.MEMBERSHIP

        # Set RecentAffected according to the sent _affected key – see (¤) in other code parts
        if "status" in data and data["status"] == FieldReport.Status.EW:  # Early Warning
            if "num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.RCRC_POTENTIALLY
            elif "gov_num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT_POTENTIALLY
            elif "other_num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.OTHER_POTENTIALLY
        else:  # Event related
            if "num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.RCRC
            elif "gov_num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT
            elif "other_num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.OTHER

        # Handle EPI Figures' Source dropdown saving
        if "epi_figures_source" in data:
            if data["epi_figures_source"] == 0 or data["epi_figures_source"] == "0":
                data["epi_figures_source"] = EPISourceChoices.MINISTRY_OF_HEALTH
            elif data["epi_figures_source"] == 1 or data["epi_figures_source"] == "1":
                data["epi_figures_source"] = EPISourceChoices.WHO
            elif data["epi_figures_source"] == 2 or data["epi_figures_source"] == "2":
                data["epi_figures_source"] = EPISourceChoices.OTHER
            else:
                data["epi_figures_source"] = None
        else:
            data["epi_figures_source"] = None

        request_choices = [
            "bulletin",
            "dref",
            "appeal",
            "rdrt",
            "fact",
            "ifrc_staff",
            "imminent_dref",
            "forecast_based_action",
            "eru_base_camp",
            "eru_basic_health_care",
            "eru_it_telecom",
            "eru_logistics",
            "eru_deployment_hospital",
            "eru_referral_hospital",
            "eru_relief",
            "eru_water_sanitation_15",
            "eru_water_sanitation_40",
            "eru_water_sanitation_20",
        ]
        for prop in request_choices:
            if prop in data:
                if data[prop] == 1 or data[prop] == "1":
                    data[prop] = RequestChoices.REQUESTED
                elif data[prop] == 2 or data[prop] == "2":
                    data[prop] = RequestChoices.PLANNED
                elif data[prop] == 3 or data[prop] == "3":
                    data[prop] = RequestChoices.COMPLETE
                else:
                    data[prop] = RequestChoices.NO

        if instance is not None:
            serializer = CreateFieldReportSerializer(instance, data=data)
        else:
            serializer = CreateFieldReportSerializer(data=data)
        return serializer

    def map_foreign_key_relations(self, data):
        # The request data object will come with a lot of relation mappings.
        # For foreign key, we want to replace instance ID's with querysets.

        # Query foreign key relations, these are attached on model save/update.
        mappings = [
            ("user", User),
            ("dtype", DisasterType),
            ("event", Event),
        ]
        for prop, model in mappings:
            if prop in data and data[prop] is not None:
                try:
                    data[prop] = model.objects.get(pk=data[prop])
                except Exception:
                    raise BadRequest("Valid %s is required" % prop)
            elif prop != "event":
                raise BadRequest("Valid %s is required" % prop)

        return data

    def map_many_to_many_relations(self, data):
        # Query many-to-many mappings. These are removed from the data object,
        # So they can be added later.
        mappings = [
            ("countries", Country),
            ("regions", Region),
            ("districts", District),
        ]

        locations = {}
        for prop, model in mappings:
            if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
                locations[prop] = list(data[prop])
            if prop in data:
                del data[prop]

        # Sources, actions, and contacts
        mappings = [
            ("actions_taken"),
            ("contacts"),
            ("sources"),
        ]

        meta = {}
        for prop in mappings:
            if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
                meta[prop] = list(data[prop])
            if prop in data:
                del data[prop]

        mappings = [("external_partners", ExternalPartner), ("supported_activities", SupportedActivity)]

        partners = {}
        for prop, model in mappings:
            if prop in data and hasattr(data[prop], "__iter__") and len(data[prop]):
                partners[prop] = list(data[prop])
            if prop in data:
                del data[prop]

        if "start_date" in data:
            data["start_date"] = datetime.strptime(data["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=utc)
        if "sit_fields_date" in data:
            data["sit_fields_date"] = datetime.strptime(data["sit_fields_date"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(
                tzinfo=utc
            )
        return data, locations, meta, partners

    def save_locations(self, instance, locations, is_update=False):
        if is_update:
            instance.districts.clear()
            instance.countries.clear()
            instance.regions.clear()
        if "districts" in locations:
            instance.districts.add(*locations["districts"])
        if "countries" in locations:
            instance.countries.add(*locations["countries"])
            # Add countries in automatically, based on regions
            countries = Country.objects.filter(pk__in=locations["countries"])
            instance.regions.add(*[country.region for country in countries if (country.region is not None)])

    def save_partners_activities(self, instance, locations, is_update=False):
        if is_update:
            instance.external_partners.clear()
            instance.supported_activities.clear()
        if "external_partners" in locations:
            instance.external_partners.add(*locations["external_partners"])
        if "supported_activities" in locations:
            instance.supported_activities.add(*locations["supported_activities"])

    def save_meta(self, fieldreport, meta, is_update=False):
        if is_update:
            ActionsTaken.objects.filter(field_report=fieldreport).delete()
            FieldReportContact.objects.filter(field_report=fieldreport).delete()
            Source.objects.filter(field_report=fieldreport).delete()

        if "actions_taken" in meta:
            for action_taken in meta["actions_taken"]:
                actions = action_taken["actions"]
                del action_taken["actions"]
                action_taken[TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME] = django_get_language()
                actions_taken = ActionsTaken.objects.create(field_report=fieldreport, **action_taken)
                CreateFieldReportSerializer.trigger_field_translation(actions_taken)
                actions_taken.actions.add(*actions)

        if "contacts" in meta:
            FieldReportContact.objects.bulk_create(
                [FieldReportContact(field_report=fieldreport, **fields) for fields in meta["contacts"]]
            )

        if "sources" in meta:
            for source in meta["sources"]:
                stype, created = SourceType.objects.get_or_create(name=source["stype"])
                source["stype"] = stype
            Source.objects.bulk_create([Source(field_report=fieldreport, **fields) for fields in meta["sources"]])


class CreateFieldReport(CreateAPIView, GenericFieldReportView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()
    serializer_class = CreateFieldReportSerializer

    def create_event(self, report):
        event = Event.objects.create(
            name=report.summary,
            dtype=report.dtype,
            summary=report.description or "",
            disaster_start_date=report.start_date,
            auto_generated=True,
            auto_generated_source=SOURCES["new_report"],
            visibility=report.visibility,
            **{TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME: django_get_language()},
        )
        CreateFieldReportSerializer.trigger_field_translation(event)
        report.event = event
        report.save()
        return event

    def create(self, request, *args, **kwargs):
        serializer = self.serialize(request.data)
        if not serializer.is_valid():
            try:
                logger.error("Create Field Report serializer errors: {}".format(serializer.errors))
            except Exception:
                logger.error("Could not log create Field Report serializer errors")
            raise BadRequest(serializer.errors)

        data = self.map_foreign_key_relations(request.data)
        data, locations, meta, partners = self.map_many_to_many_relations(data)

        try:
            # TODO: Use serializer to create fieldreport
            data[TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME] = django_get_language()
            fieldreport = FieldReport.objects.create(
                **data,
            )
            CreateFieldReportSerializer.trigger_field_translation(fieldreport)
        except Exception as e:
            try:
                err_msg = str(e)
                logger.error("Could not create Field Report.", exc_info=True)
                raise BadRequest("Could not create Field Report. Error: {}".format(err_msg))
            except Exception:
                raise BadRequest("Could not create Field Report")

        # ### Creating relations ###
        # These are *not* handled in a transaction block.
        # The data model for these is very permissive. We're more interested in the
        # Numerical data being there than not.
        errors = []
        try:
            self.save_locations(fieldreport, locations)
            self.save_partners_activities(fieldreport, partners)
        except Exception as e:
            errors.append(e)

        try:
            self.save_meta(fieldreport, meta)
        except Exception as e:
            errors.append(e)

        # If the report doesn't have an emergency attached, create one.
        if fieldreport.event is None:
            event = self.create_event(fieldreport)
            try:
                self.save_locations(event, locations)
            except Exception as e:
                errors.append(e)

        if len(errors):
            logger.error("%s errors creating new field reports" % len(errors))
            for error in errors:
                logger.error(str(error)[:200])

        return Response({"id": fieldreport.id}, status=HTTP_201_CREATED)


class UpdateFieldReport(UpdateAPIView, GenericFieldReportView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()
    serializer_class = CreateFieldReportSerializer

    def partial_update(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serialize(request.data, instance=instance)
        if not serializer.is_valid():
            raise BadRequest(serializer.errors)

        data = self.map_foreign_key_relations(request.data)
        data, locations, meta, partners = self.map_many_to_many_relations(data)

        try:
            serializer.save()
        except Exception:
            logger.error("Faild to update field report", exc_info=True)
            raise BadRequest("Could not update field report")

        errors = []
        try:
            self.save_locations(instance, locations, is_update=True)
            self.save_partners_activities(instance, partners, is_update=True)
        except Exception as e:
            errors.append(e)

        try:
            self.save_meta(instance, meta, is_update=True)
        except Exception as e:
            errors.append(e)

        if len(errors):
            logger.error("%s errors creating new field reports" % len(errors))
            for error in errors:
                logger.error(str(error)[:200])

        return Response({"id": instance.id}, status=HTTP_200_OK)


class MainContactViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = MainContactSerializer
    queryset = MainContact.objects.order_by("extent")
    search_fields = ("name", "email")  # for /docs


class NSLinksViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = NsSerializer
    queryset = Country.objects.filter(url_ifrc__contains="/").order_by("url_ifrc")


class GoHistoricalFilter(filters.FilterSet):
    countries = filters.ModelMultipleChoiceFilter(field_name="countries", queryset=Country.objects.all())
    iso3 = filters.CharFilter(field_name="countries__iso3", lookup_expr="icontains")
    region = filters.NumberFilter(field_name="countries__region", lookup_expr="exact")

    class Meta:
        model = Event
        fields = ()


class GoHistoricalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GoHistoricalSerializer
    filterset_class = GoHistoricalFilter

    def get_queryset(self):
        return Event.objects.filter(appeals__isnull=False)


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
    permission_classes = [IsAuthenticated]
    filterset_class = UserFilterSet

    def get_queryset(self):
        return User.objects.filter(is_active=True)


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
