from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django.utils import timezone
from django_filters import rest_framework as filters
from django.db.models import Count, Q
from .admin_classes import RegionRestrictedAdmin
from api.models import Country, Region
from api.serializers import (MiniCountrySerializer, NotCountrySerializer)
from django.conf import settings
from datetime import datetime
import pytz

from .models import (
    Form, FormData, FormArea, FormComponent, FormQuestion, FormAnswer, NSPhase, WorkPlan, Overview, NiceDocument, AssessmentType
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
    AssessmentTypeSerializer,
    ListNiceDocSerializer,
    FormAreaSerializer,
    FormComponentSerializer,
    FormQuestionSerializer,
    FormAnswerSerializer
)


class FormFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')

    class Meta:
        model = Form
        fields = {
            'id': ('exact',)
        }


class FormViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all().select_related('user', 'area', 'country')
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = FormFilter
    # It is not checked whether this user is the same as the saver. Maybe (for helpers) it is not needed really.

    def get_queryset(self):
        queryset = Form.objects.all()
        return (
            self.get_filtered_queryset(self.request, queryset, 1)
                .select_related('area', 'country')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormSerializer
        # else:
        #     return DetailFormSerializer
        # ordering_fields = ('name',)


class FormDataFilter(filters.FilterSet):
    form = filters.NumberFilter(field_name='form', lookup_expr='exact')
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')

    class Meta:
        model = FormData
        fields = {
            'form': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }


class FormDataViewset(viewsets.ReadOnlyModelViewSet):
    """Can use 'new' GET parameter for using data only after the last due_date"""
    # Duplicate of PERDocsViewset
    queryset = FormData.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = FormDataFilter

    def get_queryset(self):
        queryset = FormData.objects.all().select_related(
            'question',
            'selected_answer',
            'question__component',
            'question__component__area'
        ).prefetch_related(
            'question__answers'
        )
        cond1 = Q()
        cond2 = Q()
        if 'new' in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            tmz = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(form__submitted_at__gt=last_duedate)
        if 'country' in self.request.query_params.keys():
            cid = self.request.query_params.get('country', None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(form__country_id=country[0].id)
        queryset = FormData.objects.filter(cond1 & cond2)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 2)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
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
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')

    class Meta:
        model = NiceDocument
        fields = {
            'id': ('exact',),
        }


class PERDocsViewset(viewsets.ReadOnlyModelViewSet):
    """ To collect PER Documents """
    # Duplicate of FormDataViewset
    queryset = NiceDocument.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = PERDocsFilter

    def get_queryset(self):
        queryset = NiceDocument.objects.all()
        cond1 = Q()
        cond2 = Q()
        cond3 = Q()
        if 'new' in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            tmz = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = tmz.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(created_at__gt=last_duedate)
        if 'country' in self.request.query_params.keys():
            cid = self.request.query_params.get('country', None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(country_id=country[0].id)
        if 'visible' in self.request.query_params.keys():
            cond3 = Q(visibility=1)
        queryset = NiceDocument.objects.filter(cond1 & cond2 & cond3)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 4)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
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
        if self.action == 'list':
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
        queryset = Form.objects.filter(submitted_at__gt=last_duedate)
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
        queryset1 = Region.objects.all().annotate(Count('country')).values('id', 'country__count')
        queryset2 = Region.objects.filter(country__form__submitted_at__gt=last_duedate) \
            .values('id').annotate(forms_sent=Count('country', distinct=True))

        # We merge the 2 lists (all and forms_sent), like {'id': 2, 'country__count': 37} and {'id': 2, 'forms_sent': 2} to
        #                                                 {'id': 2, 'country__count': 37, 'forms_sent': 2}, even with zeroes.
        result = []
        for i in queryset1:
            i['forms_sent'] = 0
            for j in queryset2:
                if int(j['id']) == int(i['id']):
                    # if this never occurs, (so no form-sender country in this region), forms_sent remain 0
                    i['forms_sent'] = j['forms_sent']
            result.append(i)
        # [{'id': 0, 'country__count': 49, 'forms_sent': 0}, {'id': 1, 'country__count': 35, 'forms_sent': 1}...
        return result


class GlobalPreparednessViewset(viewsets.ReadOnlyModelViewSet):
    """Global Preparedness Highlights"""
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
        queryset = FormData.objects.filter(form__submitted_at__gt=last_duedate, selected_option=7).select_related('form')
        result = []
        for i in queryset:
            j = {'id': i.form.id}
            j.update({'code': i.form.code})
            j.update({'question_id': i.question_id})
            result.append(j)
        return result


class NSPhaseFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name='country', lookup_expr='exact')
    phase = filters.NumberFilter(field_name='phase', lookup_expr='exact')
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')

    class Meta:
        model = NSPhase
        fields = {
            'updated_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }


class NSPhaseViewset(viewsets.ReadOnlyModelViewSet):
    """NS PER Process Phase Viewset"""
    queryset = NSPhase.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    serializer_class = NSPhaseSerializer
    filter_class = NSPhaseFilter

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
            # If this feature is not needed in the future (2020.01.30), this section can be deleted:

            # Giving a default value when queryset is empty, with the given country_id (if exists)
            if not queryset:
                j = {'id': -1}
                country_param = self.request.query_params.get('country', None)
                if country_param and Country.objects.filter(pk=country_param):
                    j.update({'country': Country.objects.get(pk=country_param)})
                j.update({'updated_at': pytz.timezone("Europe/Zurich").localize(datetime(2011, 11, 11, 1, 1, 1, 0))})
                j.update({'phase': 0})
                return [j]
        return queryset


class WorkPlanFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')
    country = filters.NumberFilter(field_name='country', lookup_expr='exact')

    class Meta:
        model = WorkPlan
        fields = {
            'id': ('exact',),
        }


class WorkPlanViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Work Plan Viewset"""
    queryset = WorkPlan.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filter_class = WorkPlanFilter
    serializer_class = WorkPlanSerializer


class OverviewFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')
    country = filters.NumberFilter(field_name='country', lookup_expr='exact')

    class Meta:
        model = Overview
        fields = {
            'id': ('exact',),
        }


class OverviewViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Overview Viewset"""
    queryset = Overview.objects.all().select_related('country', 'user', 'type_of_ca', 'type_of_last_ca')
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filter_class = OverviewFilter
    serializer_class = OverviewSerializer


class OverviewStrictViewset(OverviewViewset):
    """ PER Overview Viewset - strict"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = OverviewSerializer

    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

    def get_queryset(self):
        queryset = Overview.objects.all()
        return (
            self.get_filtered_queryset(self.request, queryset, 4)
                .select_related('country', 'user', 'type_of_ca', 'type_of_last_ca')
        )


class AssessmentTypeViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Overview's capacity assessment types """
    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer


class FormAreaFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')
    area_num = filters.NumberFilter(field_name='area_num', lookup_expr='exact')

    class Meta:
        model = FormArea
        fields = {
            'id': ('exact',),
            'area_num': ('exact',)
        }


class FormAreaViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Form Areas Viewset """
    serializer_class = FormAreaSerializer
    queryset = FormArea.objects.all()
    filter_class = FormAreaFilter


class FormComponentViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Form Components Viewset """
    serializer_class = FormComponentSerializer
    queryset = (
        FormComponent.objects
                     .all()
                     .order_by('area__area_num', 'component_num', 'component_letter')
                     .select_related('area')
    )


class FormQuestionFilter(filters.FilterSet):
    area_id = filters.NumberFilter(field_name='component__area__id', lookup_expr='exact')

    class Meta:
        model = FormQuestion
        fields = {
            'area_id': ('exact',)
        }


class FormQuestionViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Form Questions Viewset """
    serializer_class = FormQuestionSerializer
    queryset = (
        FormQuestion.objects
                    .all()
                    .order_by('component__component_num', 'question_num')
                    .select_related('component')
                    .prefetch_related('answers')
    )
    filter_class = FormQuestionFilter


class FormAnswerViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Form Answers Viewset """
    serializer_class = FormAnswerSerializer
    queryset = FormAnswer.objects.all()
