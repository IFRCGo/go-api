from rest_framework.settings import api_settings
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
from drf_spectacular.utils import extend_schema, extend_schema_view

from .admin_classes import RegionRestrictedAdmin
from api.models import Country
from deployments.models import SectorTag
from .models import (
    FormData,
    FormArea,
    FormComponent,
    FormQuestion,
    FormAnswer,
    OrganizationTypes,
    OpsLearning,
    Overview,
    NiceDocument,
    AssessmentType,
    PerWorkPlan,
    FormPrioritization,
    PerAssessment,
    PerFile,
    PerComponentRating,
)
from .serializers import (
    LatestCountryOverviewSerializer,
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
    PerAssessmentSerializer,
    PerFileSerializer,
    PublicPerCountrySerializer,
    UserPerCountrySerializer,
    PerOptionsSerializer,
    LatestCountryOverviewInputSerializer,
    PerFileInputSerializer,
    PublicPerProcessSerializer,
    PublicPerAssessmentSerializer,
    OpsLearningSerializer,
    OpsLearningInSerializer,
    OpsLearningCSVSerializer,
    PublicOpsLearningSerializer,
)
from per.permissions import PerPermission, OpsLearningPermission
from per.filter_set import (
    PerOverviewFilter,
    PerPrioritizationFilter,
    PerWorkPlanFilter,
)
from django_filters.widgets import CSVWidget
from .custom_renderers import NarrowCSVRenderer


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
        return (
            FormComponent.objects.all()
            .order_by("area__area_num", "component_num", "component_letter")
            .select_related("area")
        )


class FormQuestionFilter(filters.FilterSet):
    area_id = filters.NumberFilter(field_name="component__area__id", lookup_expr="exact")

    class Meta:
        model = FormQuestion
        fields = {"component": ("exact",)}


class FormQuestionViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Questions Viewset"""

    serializer_class = FormQuestionSerializer
    filterset_class = FormQuestionFilter
    ordering_fields = "__all__"

    def get_queryset(self):
        return (
            FormQuestion.objects.all()
            .order_by("component__component_num", "question_num", "question")
            .select_related("component")
            .prefetch_related("answers")
        )


class FormAnswerViewset(viewsets.ReadOnlyModelViewSet):
    """PER Form Answers Viewset"""

    serializer_class = FormAnswerSerializer
    queryset = FormAnswer.objects.all()
    ordering_fields = "__all__"


@extend_schema_view(
    list=extend_schema(parameters=[LatestCountryOverviewInputSerializer], responses=LatestCountryOverviewSerializer)
)
class LatestCountryOverviewViewset(viewsets.ReadOnlyModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = LatestCountryOverviewSerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id", None)
        if country_id:
            return (
                Overview.objects.select_related("country", "type_of_assessment")
                .filter(country_id=country_id)
                .order_by("-created_at")
            )
        return Overview.objects.none()


class PerOverviewViewSet(viewsets.ModelViewSet):
    serializer_class = PerOverviewSerializer
    permission_classes = [IsAuthenticated, PerPermission]
    filterset_class = PerOverviewFilter
    ordering_fields = "__all__"
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

    def get_queryset(self):
        queryset = Overview.objects.select_related("country", "user")
        return self.get_filtered_queryset(self.request, queryset, dispatch=0)


class NewPerWorkPlanViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = PerWorkPlan.objects.all()
    serializer_class = PerWorkPlanSerializer
    filterset_class = PerWorkPlanFilter
    ordering_fields = "__all__"


class PerFormDataViewSet(viewsets.ModelViewSet):
    serializer_class = PerFormDataSerializer
    queryset = FormData.objects.all()
    ordering_fields = "__all__"


class FormPrioritizationViewSet(viewsets.ModelViewSet):
    serializer_class = FormPrioritizationSerializer
    queryset = FormPrioritization.objects.all()
    filterset_class = PerPrioritizationFilter
    permission_classes = (IsAuthenticated,)
    ordering_fields = "__all__"


class PublicFormPrioritizationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FormPrioritizationSerializer
    queryset = FormPrioritization.objects.all()
    ordering_fields = "__all__"


class PerOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = "__all__"

    @extend_schema(request=None, responses=PerOptionsSerializer)
    def get(self, request, version=None):
        return response.Response(
            PerOptionsSerializer(
                dict(
                    componentratings=PerComponentRating.objects.all(),
                    answers=FormAnswer.objects.all(),
                    overviewassessmenttypes=AssessmentType.objects.all(),
                )
            ).data
        )


class PerProcessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerProcessSerializer
    filterset_class = PerOverviewFilter
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = "__all__"
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

    def get_queryset(self):
        queryset = Overview.objects.order_by("country", "-assessment_number", "-date_of_assessment")
        return self.get_filtered_queryset(self.request, queryset, dispatch=0)


class PublicPerProcessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicPerProcessSerializer
    ordering_fields = "__all__"

    def get_queryset(self):
        return Overview.objects.order_by("country", "-assessment_number", "-date_of_assessment")


class FormAssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = PerAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = "__all__"

    def get_queryset(self):
        return PerAssessment.objects.select_related("overview")


class PublicFormAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicPerAssessmentSerializer
    ordering_fields = "__all__"

    def get_queryset(self):
        return PerAssessment.objects.select_related("overview")


class PerFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = PerFileSerializer

    def get_queryset(self):
        if self.request is None:
            return PerFile.objects.none()
        return PerFile.objects.filter(created_by=self.request.user)

    @extend_schema(request=PerFileInputSerializer, responses=PerFileSerializer(many=True))
    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = [files[0] for files in dict((request.data).lists()).values()]
        data = [{"file": file} for file in files]
        file_serializer = PerFileSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=drf_status.HTTP_201_CREATED)
        return response.Response(file_serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


class PerCountryViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer_class(self):
        user = self.request.user
        if not user.is_authenticated:
            return PublicPerCountrySerializer
        else:
            return UserPerCountrySerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id", None)
        if country_id:
            return (
                Overview.objects.select_related("country", "type_of_assessment")
                .filter(country_id=country_id)
                .order_by("-created_at")[:1]
            )
        return Overview.objects.none()


class PerAggregatedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerProcessSerializer
    filterset_class = PerOverviewFilter
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ["assessment_number", "phase", "date_of_assessment"]
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

    def get_queryset(self):
        queryset = Overview.objects.filter(
            id__in=Overview.objects.order_by(
                "country_id",
                "-assessment_number").distinct("country_id").values("id")
        )
        return self.get_filtered_queryset(self.request, queryset, dispatch=0)


class OpsLearningFilter(filters.FilterSet):
    type_validated = filters.NumberFilter(field_name='type_validated', lookup_expr='exact')
    appeal_document_id = filters.NumberFilter(field_name='appeal_document_id', lookup_expr='exact')
    organization_validated__in = filters.ModelMultipleChoiceFilter(
        label='validated_organizations',
        field_name='organization_validated',
        help_text='Organization GO identifiers, comma separated',
        widget=CSVWidget,
        queryset=OrganizationTypes.objects.all(),
    )
    sector_validated__in = filters.ModelMultipleChoiceFilter(
        label='validated_sectors',
        field_name='sector_validated',
        help_text='Sector identifiers, comma separated',
        widget=CSVWidget,
        queryset=SectorTag.objects.all(),
    )
    per_component_validated__in = filters.ModelMultipleChoiceFilter(
        label='validated_per_components',
        field_name='per_component_validated',
        help_text='PER Component identifiers, comma separated',
        widget=CSVWidget,
        queryset=FormComponent.objects.all(),
    )

    class Meta:
        model = OpsLearning
        fields = {
            'id': ('exact', 'in'),
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'modified_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'is_validated': ('exact',),
            'learning': ('exact', 'icontains'),
            'learning_validated': ('exact', 'icontains'),
            'organization_validated': ('exact',),
            'sector_validated': ('exact',),
            'per_component_validated': ('exact',),
            'appeal_code': ('exact', 'in'),
            'appeal_code__code': ('exact', 'icontains', 'in'),
            'appeal_code__num_beneficiaries': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'appeal_code__start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'appeal_code__dtype': ('exact', 'in'),
            'appeal_code__country': ('exact', 'in'),
            'appeal_code__country__name': ('exact', 'in'),
            'appeal_code__country__iso': ('exact', 'in'),
            'appeal_code__country__iso3': ('exact', 'in'),
            'appeal_code__region': ('exact', 'in'),
        }


class OpsLearningViewset(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing OpsLearning records.
    """
    queryset = OpsLearning.objects.all()
    permission_classes = [OpsLearningPermission]
    filterset_class = OpsLearningFilter
    search_fields = ('learning', 'learning_validated', 'appeal_code__code', 'appeal_code__name', 'appeal_code__name_en', 'appeal_code__name_es', 'appeal_code__name_fr', 'appeal_code__name_ar')

    def get_renderers(self):
        serializer = self.get_serializer()
        if isinstance(serializer, OpsLearningCSVSerializer):
            return [NarrowCSVRenderer()]
        return [renderer() for renderer in tuple(api_settings.DEFAULT_RENDERER_CLASSES)]

    def get_queryset(self):
        qs = super().get_queryset()
        if OpsLearning.is_user_admin(self.request.user):
            return qs.select_related('appeal_code',).prefetch_related(
                'sector', 'organization', 'per_component', 'sector_validated',
                'organization_validated', 'per_component_validated')
        return qs.filter(is_validated=True).select_related('appeal_code',).prefetch_related(
            'sector', 'organization', 'per_component', 'sector_validated',
            'organization_validated', 'per_component_validated')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            request_format = self.request.GET.get("format", "json")
            if request_format == "csv":
                return OpsLearningCSVSerializer
            elif OpsLearning.is_user_admin(self.request.user):
                return OpsLearningSerializer
            return PublicOpsLearningSerializer
        return OpsLearningInSerializer

    def get_renderer_context(self):
        context = super().get_renderer_context()
        # Force the order from the serializer. Otherwise redundant literal list

        original = ["id", "appeal_code.code", "learning", "finding", 'sector', 'per_component', 'organization',
            "appeal_code.country", "appeal_code.region", "appeal_code.dtype", "appeal_code.start_date",
            "appeal_code.num_beneficiaries", "modified_at"]
        displayed = ['id', 'appeal_code', 'learning', 'finding', 'sector', 'component', 'organization',
            'country_name', 'region_name', 'dtype_name', 'appeal_year',
            'appeal_num_beneficiaries', 'modified_at']

        context["header"] = original
        context["labels"] = {i: i for i in context["header"]}
        # We can change the column titles (called "labels"):
        for i, label in enumerate(displayed):
            context["labels"][original[i]] = label
        context["bom"] = True

        return context
