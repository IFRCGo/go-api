from datetime import datetime
import csv
import pytz
from rest_framework.authentication import TokenAuthentication

from rest_framework.permissions import IsAuthenticated
from rest_framework import (
    viewsets,
    mixins,
    views,
    response,
    permissions,
)
from rest_framework.views import APIView
from django.http import HttpResponse
from django_filters import rest_framework as filters
from django.db.models import Q

from .admin_classes import RegionRestrictedAdmin
from api.models import Country, Region
from api.views import bad_request
from api.serializers import MiniCountrySerializer, NotCountrySerializer
from django.conf import settings


from .models import (
    Form,
    FormData,
    FormArea,
    FormComponent,
    FormQuestion,
    FormAnswer,
    NSPhase,
    WorkPlan,
    Overview,
    NiceDocument,
    AssessmentType,
    PerWorkPlan,
    FormPrioritization,
    WorkPlanStatus
)

from .serializers import (
    FormStatSerializer,
    ListFormSerializer,
    ListFormWithDataSerializer,
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
)
from per.permissions import PerPermission
from per.filter_set import (
    PerOverviewFilter,
    PerPrioritizationFilter,
    PerWorkPlanFilter,
)


class FormFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    overview_id = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = Form
        fields = {"id": ("exact",), "overview_id": ("exact",)}


class FormViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all().select_related("user", "area")
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filterset_class = FormFilter
    # It is not checked whether this user is the same as the saver. Maybe (for helpers) it is not needed really.

    def get_queryset(self):
        queryset = Form.objects.all()
        return (
            self.get_filtered_queryset(self.request, queryset, 1)
            .order_by("area__area_num")
            .select_related("area", "overview")
            .prefetch_related("form_data")
        )

    def get_serializer_class(self):
        with_data = self.request.GET.get("with_data", "false")
        if with_data == "true":
            return ListFormWithDataSerializer
        if self.action == "list":
            return ListFormSerializer
        # else:
        #     return DetailFormSerializer
        # ordering_fields = ('name',)


class FormDataFilter(filters.FilterSet):
    form = filters.NumberFilter(field_name="form", lookup_expr="exact")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = FormData
        fields = {
            "form": ("exact", "gt", "gte", "lt", "lte"),
        }


class FormDataViewset(viewsets.ReadOnlyModelViewSet):
    """Can use 'new' GET parameter for using data only after the last due_date"""

    # Duplicate of PERDocsViewset
    queryset = FormData.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filterset_class = FormDataFilter

    def get_queryset(self):
        queryset = (
            FormData.objects.all()
            .select_related("question", "selected_answer", "question__component", "question__component__area")
            .prefetch_related("question__answers")
        )
        cond1 = Q()
        cond2 = Q()
        if "new" in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            tmz = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(form__updated_at__gt=last_duedate)
        if "country" in self.request.query_params.keys():
            cid = self.request.query_params.get("country", None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(form__overview__country_id=country[0].id)
        queryset = FormData.objects.filter(cond1 & cond2)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 2)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ListFormDataSerializer
        # else:
        #     return DetailFormDataSerializer
        # ordering_fields = ('name',)


class FormCountryViewset(viewsets.ReadOnlyModelViewSet):
    """shows the (PER editable) countries for a user."""

    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    serializer_class = MiniCountrySerializer

    def get_queryset(self):
        queryset = Country.objects.all()
        return self.get_filtered_queryset(self.request, queryset, 3)


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


# Not used:
# class FormCountryUsersViewset(viewsets.ReadOnlyModelViewSet):
#    """Names and email addresses of the PER responsible users in a GIVEN country.
#    Without country parameter it gives back empty set, not error."""
#    queryset = User.objects.all()
#    authentication_classes = (TokenAuthentication,)
#    permission_classes = (IsAuthenticated,)
#    serializer_class = MiniUserSerializer
#
#    def get_queryset(self):
#        country = Country.objects.filter(pk=self.request.query_params.get('country', None))
#        if country: # First we try to search a country PER admin
#            regid = country.values('region')[0]['region']
#            regionname = ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'MENA'][regid]
#            countryname = country.values('name')[0]['name']
#            cond1 = Q(groups__name__contains='PER')
#            cond2 = Q(groups__name__icontains=countryname)
#            queryset = User.objects.filter(cond1 & cond2).values('first_name', 'last_name', 'email')
#            if queryset.exists():
#                return queryset
#            else: # Now let's try to get a Region admin for that country
#                cond2 = Q(groups__name__icontains=regionname)
#                cond3 = Q(groups__name__contains='Region')
#                queryset = User.objects.filter(cond1 & cond2 & cond3).values('first_name', 'last_name', 'email')
#                if queryset.exists():
#                    return queryset
#                else: # Finally we can show only PER Core admins
#                    cond2 = Q(groups__name__contains='Core Admins') # region also can come here
#                    queryset = User.objects.filter(cond1 & cond2).values('first_name', 'last_name', 'email')
#                    if queryset.exists():
#                        return queryset
#        return User.objects.none()


class FormStatViewset(viewsets.ReadOnlyModelViewSet):
    """Shows name, code, country_id, language of filled forms"""

    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        queryset = Form.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FormStatSerializer
        # else:
        #     return DetailFormSerializer
        # ordering_fields = ('name',)


class FormPermissionViewset(viewsets.ReadOnlyModelViewSet):
    """Shows if a user has permission to PER frontend tab or not"""

    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    serializer_class = NotCountrySerializer

    def get_queryset(self):
        queryset = Country.objects.all()
        if self.get_filtered_queryset(self.request, queryset, 3).exists():
            return [Country.objects.get(id=1)]
        else:
            return Country.objects.none()


class CountryDuedateViewset(viewsets.ReadOnlyModelViewSet):
    """Countries and their forms which were submitted since last due date"""

    queryset = Form.objects.all()
    country = MiniCountrySerializer
    serializer_class = ShortFormSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        tmz = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = tmz.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        queryset = Form.objects.filter(updated_at__gt=last_duedate)
        if queryset.exists():
            return queryset
        else:
            return Form.objects.none()


class EngagedNSPercentageViewset(viewsets.ReadOnlyModelViewSet):
    """National Societies engaged in per process"""

    queryset = Region.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    serializer_class = EngagedNSPercentageSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        tmz = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = tmz.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        # FIXME: these make no sense, Region doesn't have a Country relation
        # hopefully removable after adding the dashboards
        # queryset1 = Region.objects.all().annotate(Count('country')).values('id', 'country__count')
        # queryset2 = Region.objects.filter(country__form__updated_at__gt=last_duedate) \
        #     .values('id').annotate(forms_sent=Count('country', distinct=True))

        # We merge the 2 lists (all and forms_sent), like {'id': 2, 'country__count': 37} and {'id': 2, 'forms_sent': 2} to
        #                                                 {'id': 2, 'country__count': 37, 'forms_sent': 2}, even with zeroes.
        result = []
        # FIXME: as above
        # for i in queryset1:
        #     i['forms_sent'] = 0
        #     for j in queryset2:
        #         if int(j['id']) == int(i['id']):
        #             # if this never occurs, (so no form-sender country in this region), forms_sent remain 0
        #             i['forms_sent'] = j['forms_sent']
        #     result.append(i)
        # [{'id': 0, 'country__count': 49, 'forms_sent': 0}, {'id': 1, 'country__count': 35, 'forms_sent': 1}...
        return result


class GlobalPreparednessViewset(viewsets.ReadOnlyModelViewSet):
    """Global Preparedness Highlights"""

    # Probably not used. E.g. no 'code' in Form
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = GlobalPreparednessSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        tmz = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = tmz.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        queryset = FormData.objects.filter(form__updated_at__gt=last_duedate, selected_answer_id=7).select_related("form")
        result = []
        # for i in queryset:
        #     j = {'id': i.form.id}
        #     j.update({'code': i.form.code})
        #     j.update({'question_id': i.question_id})
        #     result.append(j)
        return result


class NSPhaseFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")
    phase = filters.NumberFilter(field_name="phase", lookup_expr="exact")
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = NSPhase
        fields = {
            "updated_at": ("exact", "gt", "gte", "lt", "lte"),
        }


class NSPhaseViewset(viewsets.ReadOnlyModelViewSet):
    """NS PER Process Phase Viewset"""

    queryset = NSPhase.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    serializer_class = NSPhaseSerializer
    filterset_class = NSPhaseFilter

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
            # If this feature is not needed in the future (2020.01.30), this section can be deleted:

            # Giving a default value when queryset is empty, with the given country_id (if exists)
            if not queryset:
                j = {"id": -1}
                country_param = self.request.query_params.get("country", None)
                if country_param and Country.objects.filter(pk=country_param):
                    j.update({"country": Country.objects.get(pk=country_param)})
                j.update({"updated_at": pytz.timezone("Europe/Zurich").localize(datetime(2011, 11, 11, 1, 1, 1, 0))})
                j.update({"phase": 0})
                return [j]
        return queryset


class WorkPlanFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = WorkPlan
        fields = {
            "id": ("exact",),
        }


class WorkPlanViewset(viewsets.ReadOnlyModelViewSet):
    """PER Work Plan Viewset"""

    queryset = WorkPlan.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filterset_class = WorkPlanFilter
    serializer_class = WorkPlanSerializer


class OverviewFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country", lookup_expr="exact")

    class Meta:
        model = Overview
        fields = {"id": ("exact",), "country": ("exact",)}


class OverviewViewset(viewsets.ReadOnlyModelViewSet):
    """PER Overview Viewset"""

    queryset = (
        Overview.objects.all()
        .select_related("country", "user", "type_of_assessment")
        .prefetch_related("forms")
        .order_by("country__name", "-updated_at")
    )
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filterset_class = OverviewFilter
    serializer_class = OverviewSerializer


class OverviewStrictViewset(OverviewViewset):
    """PER Overview Viewset - strict"""

    # authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = OverviewSerializer

    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

    def get_queryset(self):
        queryset = Overview.objects.all()
        return (
            self.get_filtered_queryset(self.request, queryset, 4)
            .select_related("country", "user", "type_of_assessment")
            .order_by("country__name", "-updated_at")
        )


class AssessmentTypeViewset(viewsets.ReadOnlyModelViewSet):
    """PER Overview's capacity assessment types"""

    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer


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
    queryset = (
        FormQuestion.objects.all()
        .order_by("component__component_num", "question_num", "question")
        .select_related("component")
        .prefetch_related("answers")
    )

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
    authentication_classes = (TokenAuthentication,)
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
        return None


class ExportAssessmentToCSVViewset(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = LatestCountryOverviewSerializer
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions

    def get(self, request):
        # TODO: Add Overview data too
        overview_id = request.GET.get("overview_id", None)
        if not overview_id:
            return bad_request("Could not complete request, 'overview_id' is missing.")

        ov = Overview.objects.filter(id=overview_id).first()
        if not ov:
            return bad_request("Could not find an Overview with the provided 'overview_id'.")

        # Check if the User has permissions to update
        if not request.user.is_superuser and not request.user.has_perm("api.per_core_admin"):
            countries, regions = self.get_request_user_regions(request)

            if ov:
                # These need to be strings
                ov_country = f"{ov.country.id}" or ""
                ov_region = f"{ov.country.region.id}" if ov.country.region else ""

                if ov_country not in countries and ov_region not in regions:
                    return bad_request("You don't have permission to update these forms.")
            else:
                return bad_request("You don't have permission to update these forms.")

        response = HttpResponse(content_type="text/csv")
        writer = csv.writer(response)
        writer.writerow(["component number", "question number", "benchmark/epi?", "answer", "notes"])

        form_data = (
            FormData.objects.select_related("form", "form__overview", "question", "question__component", "selected_answer")
            .filter(form__overview__id=ov.id)
            .order_by(
                "question__component__component_num", "question__question_num", "question__is_epi", "question__is_benchmark"
            )
        )
        for fd in form_data:
            bench_epi = ""
            if fd.question.is_benchmark:
                bench_epi = "benchmark"
            if fd.question.is_epi:
                bench_epi = "epi"
            writer.writerow(
                [
                    fd.question.component.component_num,
                    fd.question.question_num,
                    bench_epi,
                    fd.selected_answer.text if fd.selected_answer else "",
                    fd.notes,
                ]
            )

        response["Content-Disposition"] = f"attachment; filename=assessment_{ov.id}.csv"

        return response


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

    def get(self, request, version=None):
        options = {
            'formcomponentstatus': [{"key": status.value, "value": status.label} for status in FormComponent.FormComponentStatus],
            'workplanstatus': [{"key": status.value, "value": status.label} for status in WorkPlanStatus]
        }
        return response.Response(options)


class PerProcessStatusViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerProcessSerializer
    # filterset_class = PerProcessFilterSet
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Overview.objects.order_by('-date_of_orientation')
