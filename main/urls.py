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
router.register(r'action', api_views.ActionViewset)
router.register(r'disaster_type', api_views.DisasterTypeViewset)
router.register(r'region', api_views.RegionViewset, base_name='region')
router.register(r'country', api_views.CountryViewset, base_name='country')
router.register(r'region_key_figure', api_views.RegionKeyFigureViewset, base_name='region_key_figure')
router.register(r'country_key_figure', api_views.CountryKeyFigureViewset, base_name='country_key_figure')
router.register(r'region_snippet', api_views.RegionSnippetViewset, base_name='region_snippet')
router.register(r'country_snippet', api_views.CountrySnippetViewset, base_name='country_snippet')
router.register(r'district', api_views.DistrictViewset)
router.register(r'event', api_views.EventViewset, base_name='event')
router.register(r'event_snippet', api_views.EventSnippetViewset, base_name='event_snippet')
router.register(r'situation_report', api_views.SituationReportViewset, base_name='situation_report')
router.register(r'situation_report_type', api_views.SituationReportTypeViewset)
router.register(r'appeal', api_views.AppealViewset)
router.register(r'appeal_document', api_views.AppealDocumentViewset)
router.register(r'profile', api_views.ProfileViewset, base_name='profile')
router.register(r'user', api_views.UserViewset, base_name='user')
router.register(r'field_report', api_views.FieldReportViewset, base_name='field_report')
router.register(r'eru', deployment_views.ERUViewset)
router.register(r'featured_event_deployments', api_views.EventDeploymentsViewset, base_name='featured_event_deployments')
router.register(r'eru_owner', deployment_views.ERUOwnerViewset)
router.register(r'personnel_deployment', deployment_views.PersonnelDeploymentViewset)
router.register(r'personnel', deployment_views.PersonnelViewset)
router.register(r'partner_deployment', deployment_views.PartnerDeploymentViewset)
router.register(r'surge_alert', notification_views.SurgeAlertViewset)
router.register(r'subscription', notification_views.SubscriptionViewset, base_name='subscription')
router.register(r'per', per_views.FormViewset, base_name='per')
router.register(r'perdata', per_views.FormDataViewset)
router.register(r'perdocs', per_views.PERDocsViewset)
router.register(r'percountry', per_views.FormCountryViewset, base_name='percountry')
# router.register(r'percountryusers', per_views.FormCountryUsersViewset)
router.register(r'perstat', per_views.FormStatViewset, base_name='perstat')
router.register(r'perworkplan', per_views.WorkPlanViewset)
router.register(r'peroverview', per_views.OverviewViewset, base_name='peroverview')
router.register(r'peroverviewstrict', per_views.OverviewStrictViewset, base_name='peroverviewstrict')
router.register(r'per_mission', per_views.FormPermissionViewset, base_name='per_mission')
router.register(r'per-formarea', per_views.FormAreaViewset, base_name='per-formarea')
router.register(r'per-formcomponent', per_views.FormComponentViewset, base_name='per-formcomponent')
router.register(r'per-formquestion', per_views.FormQuestionViewset, base_name='per-formquestion')
router.register(r'per-formanswer', per_views.FormAnswerViewset, base_name='per-formanswer')
router.register(r'per-assessmenttype', per_views.AssessmentTypeViewset, base_name='per-assessmenttype')
router.register(r'per_country_duedate', per_views.CountryDuedateViewset)
router.register(r'per_engaged_ns_percentage', per_views.EngagedNSPercentageViewset, base_name='per_engaged_ns_percentage')
router.register(r'per_global_preparedness', per_views.GlobalPreparednessViewset, base_name='per_global_preparedness')
router.register(r'per_ns_phase', per_views.NSPhaseViewset)
# router.register(r'latest_country_overviews', api_views.LatestCountryOverviewViewset, base_name='latest_country_overviews')
router.register(r'regional-project', deployment_views.RegionalProjectViewset)
router.register(r'project', deployment_views.ProjectViewset)
router.register(r'data-bank/country-overview', CountryOverviewViewSet)
router.register(r'region-project', deployment_views.RegionProjectViewset, base_name='region-project')
router.register(r'domainwhitelist', registration_views.DomainWhitelistViewset)
router.register(r'language', lang_views.LanguageViewSet, base_name='language')


admin.site.site_header = 'IFRC Go administration'
admin.site.site_title = 'IFRC Go admin'

urlpatterns = [
    url(r'^api/v1/es_search/', EsPageSearch.as_view()),
    url(r'^api/v1/es_health/', EsPageHealth.as_view()),
    url(r'^api/v1/graphql/', GraphQLView.as_view(graphiql=True)),
    url(r'^api/v1/aggregate/', AggregateByTime.as_view()),
    url(r'^api/v1/aggregate_dtype/', AggregateByDtype.as_view()),
    url(r'^api/v1/aggregate_area/', AreaAggregate.as_view()),
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
