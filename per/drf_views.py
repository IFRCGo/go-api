from datetime import datetime
import pytz
from rest_framework.authentication import TokenAuthentication

from rest_framework.permissions import IsAuthenticated
from rest_framework import (
    viewsets,
    views,
    response,
    permissions,
    mixins,
    status as drf_status,
)
from rest_framework.decorators import action
from django_filters import rest_framework as filters
from django.db.models import Q
from django.conf import settings
from drf_spectacular.utils import extend_schema

from .admin_classes import RegionRestrictedAdmin
from api.models import Country
from .models import (
    FormData,
    FormArea,
    FormComponent,
    FormQuestion,
    FormAnswer,
    Overview,
    NiceDocument,
    AssessmentType,
    PerWorkPlan,
    FormPrioritization,
    WorkPlanStatus,
    PerAssessment,
    PerFile,
    PerComponentRating
)
from .serializers import (
    FormStatSerializer,
    ListFormSerializer,
    ListFormDataSerializer,
    ShortFormSerializer,
    EngagedNSPercentageSerializer,
    GlobalPreparednessSerializer,
    NSPhaseSerializer,
    WorkPlanSerializer,
    OverviewSerializer,
    LatestCountryOverviewSerializer,
    AssessmentTypeSerializer,
    ListNiceDocSerializer,
    FormAreaSerializer,
    FormComponentSerializer,
    FormQuestionSerializer,
    FormAnswerSerializer,
    PerOverviewSerializer,
    PerWorkPlanSerializer,
    PerFormDataSerializer,
    FormPrioritizationSerializer,
    PerProcessSerializer,
    FormAsessmentSerializer,
    PerAssessmentSerializer,
    PerFileSerializer,
    PublicPerCountrySerializer,
    UserPerCountrySerializer,
    PerComponentRatingSerializer,
    PerOptionsSerializer
)
from per.permissions import PerPermission
from per.filter_set import (
    PerOverviewFilter,
    PerPrioritizationFilter,
    PerWorkPlanFilter,
)


class PERDocsFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = NiceDocument
        fields = {
            "id": ("exact",),
        }


class PERDocsViewset(viewsets.ReadOnlyModelViewSet):
    """To collect PER Documents"""

    # Duplicate of FormDataViewset
    queryset = NiceDocument.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filterset_class = PERDocsFilter

    def get_queryset(self):
        queryset = NiceDocument.objects.all()
        cond1 = Q()
        cond2 = Q()
        cond3 = Q()
        if "new" in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            tmz = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(created_at__gt=last_duedate)
        if "country" in self.request.query_params.keys():
            cid = self.request.query_params.get("country", None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(country_id=country[0].id)
        if "visible" in self.request.query_params.keys():
            cond3 = Q(visibility=1)
        queryset = NiceDocument.objects.filter(cond1 & cond2 & cond3)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 4)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ListNiceDocSerializer
        # else:
        #     return DetailFormDataSerializer
        # ordering_fields = ('name', 'country',)


class FormAreaFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    area_num = filters.NumberFilter(field_name="area_num", lookup_expr="exact")

    class Meta:
        model = FormArea
        fields = {"id": ("exact",), "area_num": ("exact",)}


class FormAreaViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Areas Viewset"""

    serializer_class = FormAreaSerializer
    queryset = FormArea.objects.all().order_by("area_num")
    filterset_class = FormAreaFilter


class FormComponentFilter(filters.FilterSet):
    area_id = filters.NumberFilter(field_name="area__id", lookup_expr="exact")

    class Meta:
        model = FormComponent
        fields = {"area": ("exact",)}


class FormComponentViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Components Viewset"""

    serializer_class = FormComponentSerializer
    filterset_class = FormComponentFilter

    def get_queryset(self):
        return FormComponent.objects.all().order_by(
            "area__area_num",
            "component_num",
            "component_letter"
        ).select_related("area")


class FormQuestionFilter(filters.FilterSet):
    area_id = filters.NumberFilter(field_name="component__area__id", lookup_expr="exact")

    class Meta:
        model = FormQuestion
        fields = {"component": ("exact",)}


class FormQuestionViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Questions Viewset"""

    serializer_class = FormQuestionSerializer
    filterset_class = FormQuestionFilter

    def get_queryset(self):
        return FormQuestion.objects.all()\
            .order_by("component__component_num", "question_num", "question")\
            .select_related("component")\
            .prefetch_related("answers")


class FormAnswerViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Answers Viewset"""

    serializer_class = FormAnswerSerializer
    queryset = FormAnswer.objects.all()


class LatestCountryOverviewViewset(viewsets.ReadOnlyModelViewSet):
    # authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LatestCountryOverviewSerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id", None)

        if country_id:
            return (
                Overview.objects.select_related("country", "type_of_assessment")
                .filter(country_id=country_id)
                .order_by("-created_at")[:1]  # first() gives error for len() and count()
            )
        return {}


class PerOverviewViewSet(viewsets.ModelViewSet):
    queryset = Overview.objects.select_related('country', 'user')
    serializer_class = PerOverviewSerializer
    permission_classes = [IsAuthenticated, PerPermission]
    filterset_class = PerOverviewFilter


class NewPerWorkPlanViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = PerWorkPlan.objects.all()
    serializer_class = PerWorkPlanSerializer
    filterset_class = PerWorkPlanFilter


class PerFormDataViewSet(viewsets.ModelViewSet):
    serializer_class = PerFormDataSerializer
    queryset = FormData.objects.all()


class FormPrioritizationViewSet(viewsets.ModelViewSet):
    serializer_class = FormPrioritizationSerializer
    queryset = FormPrioritization.objects.all()
    filterset_class = PerPrioritizationFilter


class PerOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses=PerOptionsSerializer)
    def get(self, request, version=None):
        return response.Response(
            PerOptionsSerializer(
                dict(
                    componentratings=PerComponentRating.objects.all(),
                    answers=FormAnswer.objects.all(),
                    overviewassessmenttypes=AssessmentType.objects.all()
                )
            ).data
        )


class PerProcessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerProcessSerializer
    filterset_class = PerOverviewFilter
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Overview.objects.order_by('country', '-assessment_number', '-date_of_assessment')


class FormAssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = PerAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PerAssessment.objects.select_related('overview')


class PerFileViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = PerFileSerializer

    def get_queryset(self):
        if self.request is None:
            return PerFile.objects.none()
        return PerFile.objects.filter(created_by=self.request.user)

    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = [
            files[0]
            for files in dict((request.data).lists()).values()
        ]
        data = [{"file": file} for file in files]
        file_serializer = PerFileSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=drf_status.HTTP_201_CREATED)
        return response.Response(file_serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


class PerCountryViewSet(
    viewsets.ReadOnlyModelViewSet
):

    def get_serializer_class(self):
        user = self.request.user
        if not user.is_authenticated:
            return PublicPerCountrySerializer
        else:
            return UserPerCountrySerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id", None)
        if country_id:
            return Overview.objects.select_related(
                "country",
                "type_of_assessment"
            ).filter(
                country_id=country_id
            ).order_by("-created_at")[:1]
        return {}


class PerAggregatedViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = PerProcessSerializer
    filterset_class = PerOverviewFilter
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['assessment_number', 'phase', 'date_of_assessment']

    def get_queryset(self):
        return Overview.objects.filter(
            id__in=Overview.objects.order_by(
                'country_id',
                '-assessment_number'
            ).distinct('country_id').values('id'))
