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
from django.contrib import admin
from graphene_django.views import GraphQLView
from tastypie.api import Api
from api.views import (
    GetAuthToken,
    ChangePassword,
    RecoverPassword,
    EsPageSearch,
    EsPageHealth,
    AggregateByDtype,
    AggregateByTime,
    UpdateSubscriptionPreferences,
    AreaAggregate,
)
from registrations.views import (
    NewRegistration,
    VerifyEmail,
    ValidateUser,
)

# DRF routes
from rest_framework import routers
from rest_framework.documentation import include_docs_urls
from api import drf_views as api_views
from deployments import drf_views as deployment_views
from notifications import drf_views as notification_views

router = routers.DefaultRouter()
router.register(r'disaster_type', api_views.DisasterTypeViewset)
router.register(r'region', api_views.RegionViewset)
router.register(r'country', api_views.CountryViewset)
router.register(r'region_key_figure', api_views.RegionKeyFigureViewset, base_name='region_key_figure')
router.register(r'country_key_figure', api_views.CountryKeyFigureViewset, base_name='country_key_figure')
router.register(r'region_snippet', api_views.RegionSnippetViewset, base_name='region_snippet')
router.register(r'country_snippet', api_views.CountrySnippetViewset, base_name='country_snippet')
router.register(r'district', api_views.DistrictViewset)
router.register(r'event', api_views.EventViewset)
router.register(r'event_snippet', api_views.EventSnippetViewset, base_name='event_snippet')
router.register(r'situation_report', api_views.SituationReportViewset, base_name='situation_report')
router.register(r'situation_report_type', api_views.SituationReportTypeViewset)
router.register(r'appeal', api_views.AppealViewset)
router.register(r'appeal_document', api_views.AppealDocumentViewset)
router.register(r'profile', api_views.ProfileViewset, base_name='profile')
router.register(r'user', api_views.UserViewset, base_name='user')
router.register(r'field_report', api_views.FieldReportViewset, base_name='field_report')

router.register(r'eru', deployment_views.ERUViewset)
router.register(r'eru_owner', deployment_views.ERUOwnerViewset)
router.register(r'personnel_deployment', deployment_views.PersonnelDeploymentViewset)
router.register(r'personnel', deployment_views.PersonnelViewset)
router.register(r'partner_deployment', deployment_views.PartnerDeploymentViewset)

router.register(r'surge_alert', notification_views.SurgeAlertViewset)
router.register(r'subscription', notification_views.SubscriptionViewset, base_name='subscription')

admin.site.site_header = 'IFRC Go administration'
admin.site.site_title = 'IFRC Go admin'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
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
    url(r'^register', NewRegistration.as_view()),
    url(r'^verify_email', VerifyEmail.as_view()),
    url(r'^validate_user', ValidateUser.as_view()),
    url(r'^change_password', ChangePassword.as_view()),
    url(r'^recover_password', RecoverPassword.as_view()),

    url(r'^api/v2/', include(router.urls)),
    url(r'^docs/', include_docs_urls(title='IFRC Go API')),
]
