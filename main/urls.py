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
from api.resources import (
    CountryResource,
    RegionResource,
    DisasterTypeResource,
    EventResource,
    SituationReportResource,
    AppealResource,
    AppealDocumentResource,
    FieldReportResource,
    UserResource,
)
from deployments.resources import (
    ERUResource,
    ERUOwnerResource,
    HeopResource,
    FactResource,
    RdrtResource,
)
from notifications.resources import SurgeAlertResource
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

# Api resources
v1_api = Api(api_name='v1')
v1_api.register(CountryResource())
v1_api.register(RegionResource())
v1_api.register(DisasterTypeResource())
v1_api.register(EventResource())
v1_api.register(SituationReportResource())
v1_api.register(AppealResource())
v1_api.register(AppealDocumentResource())
v1_api.register(FieldReportResource())
v1_api.register(UserResource())
v1_api.register(ERUResource())
v1_api.register(ERUOwnerResource())
v1_api.register(HeopResource())
v1_api.register(FactResource())
v1_api.register(RdrtResource())

# Notification resources
v1_api.register(SurgeAlertResource())

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/v1/es_search/', EsPageSearch.as_view()),
    url(r'^api/v1/graphql/', GraphQLView.as_view(graphiql=True)),
    url(r'^api/v1/aggregate/', AggregateByTime.as_view()),
    url(r'^api/v1/aggregate_dtype/', AggregateByDtype.as_view()),
    url(r'^api/v1/aggregate_area/', AreaAggregate.as_view()),
    url(r'^get_auth_token', GetAuthToken.as_view()),
    url(r'^notifications', UpdateSubscriptionPreferences.as_view()),
    url(r'^register', NewRegistration.as_view()),
    url(r'^verify_email', VerifyEmail.as_view()),
    url(r'^validate_user', ValidateUser.as_view()),
    url(r'^change_password', ChangePassword.as_view()),
    url(r'^recover_password', RecoverPassword.as_view()),
]
