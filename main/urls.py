"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from django.urls import path
from django.contrib import admin
from django.views.generic import RedirectView
from graphene_django.views import GraphQLView
from django.conf.urls.i18n import i18n_patterns
from api.views import (
    GetAuthToken,
    ChangePassword,
    RecoverPassword,
    ShowUsername,
    EsPageSearch,
    EsPageHealth,
    AggregateHeaderFigures,
    AggregateByDtype,
    AggregateByTime,
    AddSubscription,
    DelSubscription,
    UpdateSubscriptionPreferences,
    AreaAggregate,
    AddCronJobLog,
    DummyHttpStatusError,
    DummyExceptionError,
    ResendValidation
)
from registrations.views import (
    NewRegistration,
    VerifyEmail,
    ValidateUser
)
from per.views import (
    # CreatePerForm,
    UpdatePerForm,
    UpdatePerForms,
    # DeletePerForm,
    WorkPlanSent,
    CreatePerOverview,
    UpdatePerOverview,
    DeletePerOverview,
    DelWorkPlan
)
from databank.views import CountryOverviewViewSet

# DRF routes
from rest_framework import routers
from rest_framework.documentation import include_docs_urls
from api import drf_views as api_views
from per import drf_views as per_views
from deployments import drf_views as deployment_views
from notifications import drf_views as notification_views
from registrations import drf_views as registration_views
from lang import views as lang_views

router = routers.DefaultRouter()
router.register(r'action', api_views.ActionViewset, basename='action')
router.register(r'appeal', api_views.AppealViewset, basename='appeal')
router.register(r'appeal_document', api_views.AppealDocumentViewset, basename='appeal_document')
router.register(r'country', api_views.CountryViewset, basename='country')
router.register(r'country_key_figure', api_views.CountryKeyFigureViewset, basename='country_key_figure')
router.register(r'country_snippet', api_views.CountrySnippetViewset, basename='country_snippet')
router.register(r'data-bank/country-overview', CountryOverviewViewSet)
router.register(r'disaster_type', api_views.DisasterTypeViewset, basename='disaster_type')
router.register(r'district', api_views.DistrictViewset, basename='district')
router.register(r'domainwhitelist', registration_views.DomainWhitelistViewset)
router.register(r'eru', deployment_views.ERUViewset, basename='eru')
router.register(r'eru_owner', deployment_views.ERUOwnerViewset, basename='eru_owner')
router.register(r'event', api_views.EventViewset, basename='event')
router.register(r'featured_event_deployments', api_views.EventDeploymentsViewset, basename='featured_event_deployments')
router.register(r'field_report', api_views.FieldReportViewset, basename='field_report')
router.register(r'event_snippet', api_views.EventSnippetViewset, basename='event_snippet')
router.register(r'external_partner', api_views.ExternalPartnerViewset, basename='external_partner')
router.register(r'language', lang_views.LanguageViewSet, basename='language')
router.register(r'latest_country_overview', per_views.LatestCountryOverviewViewset, basename='latest_country_overview')
router.register(r'main_contact', api_views.MainContactViewset, basename='main_contact')
router.register(r'partner_deployment', deployment_views.PartnerDeploymentViewset, basename='pertner_deployment')
router.register(r'per', per_views.FormViewset, basename='per')
router.register(r'percountry', per_views.FormCountryViewset, basename='percountry')
router.register(r'perdata', per_views.FormDataViewset)
router.register(r'perdocs', per_views.PERDocsViewset)
# router.register(r'percountryusers', per_views.FormCountryUsersViewset)
router.register(r'peroverview', per_views.OverviewViewset, basename='peroverview')
router.register(r'peroverviewstrict', per_views.OverviewStrictViewset, basename='peroverviewstrict')
router.register(r'personnel_deployment', deployment_views.PersonnelDeploymentViewset, basename='personnel_deployment')
router.register(r'personnel', deployment_views.PersonnelViewset, basename='personnel')
router.register(r'personnel_by_event', api_views.DeploymentsByEventViewset, basename='personnel_by_event')
router.register(r'perstat', per_views.FormStatViewset, basename='perstat')
router.register(r'perworkplan', per_views.WorkPlanViewset)
router.register(r'per_country_duedate', per_views.CountryDuedateViewset)
router.register(r'per_engaged_ns_percentage', per_views.EngagedNSPercentageViewset, basename='per_engaged_ns_percentage')
router.register(r'per_global_preparedness', per_views.GlobalPreparednessViewset, basename='per_global_preparedness')
router.register(r'per_mission', per_views.FormPermissionViewset, basename='per_mission')
router.register(r'per_ns_phase', per_views.NSPhaseViewset)
router.register(r'per-assessmenttype', per_views.AssessmentTypeViewset, basename='per-assessmenttype')
router.register(r'per-formanswer', per_views.FormAnswerViewset, basename='per-formanswer')
router.register(r'per-formarea', per_views.FormAreaViewset, basename='per-formarea')
router.register(r'per-formcomponent', per_views.FormComponentViewset, basename='per-formcomponent')
router.register(r'per-formquestion', per_views.FormQuestionViewset, basename='per-formquestion')
router.register(r'profile', api_views.ProfileViewset, basename='profile')
router.register(r'project', deployment_views.ProjectViewset)
router.register(r'region', api_views.RegionViewset, basename='region')
router.register(r'region_key_figure', api_views.RegionKeyFigureViewset, basename='region_key_figure')
router.register(r'region_snippet', api_views.RegionSnippetViewset, basename='region_snippet')
router.register(r'region-project', deployment_views.RegionProjectViewset, basename='region-project')
router.register(r'regional-project', deployment_views.RegionalProjectViewset)
router.register(r'supported_activity', api_views.SupportedActivityViewset, basename='supported_activity')
router.register(r'situation_report', api_views.SituationReportViewset, basename='situation_report')
router.register(r'situation_report_type', api_views.SituationReportTypeViewset, basename='situation_report_type')
router.register(r'subscription', notification_views.SubscriptionViewset, basename='subscription')
router.register(r'surge_alert', notification_views.SurgeAlertViewset, basename='surge_alert')
router.register(r'user', api_views.UserViewset, basename='user')


admin.site.site_header = 'IFRC Go administration'
admin.site.site_title = 'IFRC Go admin'

urlpatterns = [
    url(r'^api/v1/es_search/', EsPageSearch.as_view()),
    url(r'^api/v1/es_health/', EsPageHealth.as_view()),
    url(r'^api/v1/graphql/', GraphQLView.as_view(graphiql=True)),
    url(r'^api/v1/aggregate/', AggregateByTime.as_view()),
    url(r'^api/v1/aggregate_dtype/', AggregateByDtype.as_view()),
    url(r'^api/v1/aggregate_area/', AreaAggregate.as_view()),
    url(r'^api/v2/appeal/aggregated', AggregateHeaderFigures.as_view()),
    url(r'^api/v2/create_field_report/', api_views.CreateFieldReport.as_view()),
    url(r'^api/v2/update_field_report/(?P<pk>\d+)/', api_views.UpdateFieldReport.as_view()),
    url(r'^get_auth_token', GetAuthToken.as_view()),
    url(r'^api/v2/update_subscriptions/', UpdateSubscriptionPreferences.as_view()),
    url(r'^api/v2/add_subscription/', AddSubscription.as_view()),
    url(r'^api/v2/del_subscription/', DelSubscription.as_view()),
    url(r'^api/v2/add_cronjob_log/', AddCronJobLog.as_view()),
    url(r'^register', NewRegistration.as_view()),
    # url(r'^createperform', CreatePerForm.as_view()),
    url(r'^updateperform', UpdatePerForm.as_view()),
    url(r'^updatemultipleperforms', UpdatePerForms.as_view()),
    # url(r'^deleteperform', DeletePerForm.as_view()),
    url(r'^createperoverview', CreatePerOverview.as_view()),
    url(r'^updateperoverview', UpdatePerOverview.as_view()),
    url(r'^deleteperoverview', DeletePerOverview.as_view()),
    url(r'^sendperworkplan', WorkPlanSent.as_view()),
    url(r'^api/v2/del_perworkplan', DelWorkPlan.as_view()),
    url(r'^verify_email', VerifyEmail.as_view()),
    url(r'^validate_user', ValidateUser.as_view()),
    url(r'^change_password', ChangePassword.as_view()),
    url(r'^recover_password', RecoverPassword.as_view()),
    url(r'^show_username', ShowUsername.as_view()),
    url(r'^resend_validation', ResendValidation.as_view()),
    url(r'^api/v2/', include(router.urls)),
    url(r'^api/v2/event/(?P<pk>\d+)', api_views.EventViewset.as_view({'get': 'retrieve'})),
    url(r'^api/v2/event/(?P<slug>[-\w]+)', api_views.EventViewset.as_view({'get': 'retrieve'}, lookup_field='slug')),
    url(r'^api/v2/exportperresults/', per_views.ExportAssessmentToCSVViewset.as_view()),
    url(r'^docs/', include_docs_urls(title='IFRC Go API')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin/', RedirectView.as_view(url='/')),
    # url(r'^', admin.site.urls),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    url(r'^server-error-for-devs', DummyHttpStatusError.as_view()),
    url(r'^exception-error-for-devs', DummyExceptionError.as_view()),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns

# API With language URL patterns
urlpatterns += i18n_patterns(
    path('', admin.site.urls),
    # NOTE: Current language switcher will not work if set to False.
    # TODO: Fix admin panel language switcher before enabling switcher in production
    prefix_default_language=True,
)
