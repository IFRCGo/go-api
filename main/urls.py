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
from api import drf_views as api_views
from deployments import drf_views as deployment_views
from notifications import drf_views as notification_views

router = routers.DefaultRouter()
router.register(r'disaster_type', api_views.DisasterTypeViewset)
router.register(r'region', api_views.RegionViewset)
router.register(r'country', api_views.CountryViewset)
router.register(r'event', api_views.EventViewset)
router.register(r'situation_report', api_views.SituationReportViewset)
router.register(r'appeal', api_views.AppealViewset)
router.register(r'appeal_document', api_views.AppealDocumentViewset)
router.register(r'profile', api_views.ProfileViewset, base_name='profile')
router.register(r'user', api_views.UserViewset, base_name='user')
router.register(r'field_report', api_views.FieldReportViewset, base_name='field_report')

router.register(r'eru', deployment_views.ERUViewset)
router.register(r'eru_owner', deployment_views.ERUOwnerViewset)
router.register(r'heop', deployment_views.HeopViewset)
router.register(r'fact', deployment_views.FactViewset)
router.register(r'rdrt', deployment_views.RdrtViewset)
router.register(r'fact_person', deployment_views.FactPersonViewset)
router.register(r'rdrt_person', deployment_views.RdrtPersonViewset)

router.register(r'surge_alert', notification_views.SurgeAlertViewset)
router.register(r'subscription', notification_views.SubscriptionViewset, base_name='subscription')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/es_search/', EsPageSearch.as_view()),
    url(r'^api/v1/graphql/', GraphQLView.as_view(graphiql=True)),
    url(r'^api/v1/aggregate/', AggregateByTime.as_view()),
    url(r'^api/v1/aggregate_dtype/', AggregateByDtype.as_view()),
    url(r'^api/v1/aggregate_area/', AreaAggregate.as_view()),
    url(r'^get_auth_token', GetAuthToken.as_view()),
    url(r'^api/v2/update_subscriptions/', UpdateSubscriptionPreferences.as_view()),
    url(r'^register', NewRegistration.as_view()),
    url(r'^verify_email', VerifyEmail.as_view()),
    url(r'^validate_user', ValidateUser.as_view()),
    url(r'^change_password', ChangePassword.as_view()),
    url(r'^recover_password', RecoverPassword.as_view()),

    url(r'^api/v2/', include(router.urls)),
]
