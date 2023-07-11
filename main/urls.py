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
In case of an api endpoint search, grep url_path in other files also, e.g:
    grep url_path $(ls */*views.py)
"""
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf.urls import url, include
from django.conf import settings
from django.urls import path
from django.contrib import admin
from django.conf.urls import static
from django.views.static import serve
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
    Brief,
    ERUTypes,
    RecentAffecteds,
    FieldReportStatuses,
    ProjectProgrammeTypes,
    ProjectPrimarySectors,
    ProjectSecondarySectors,
    ProjectOperationTypes,
    ProjectStatuses,
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
    ResendValidation,
    HayStackSearch,
)
from registrations.views import (
    VerifyEmail,
    ValidateUser,
)
from registrations.views import VerifyEmail, ValidateUser
from registrations.drf_views import RegistrationView
from per.views import (
    # CreatePerForm,
    UpdatePerForm,
    UpdatePerForms,
    # DeletePerForm,
    WorkPlanSent,
    CreatePerOverview,
    UpdatePerOverview,
    DeletePerOverview,
    DelWorkPlan,
)
from databank.views import CountryOverviewViewSet
from local_units.views import LocalUnitListAPIView, LocalUnitDetailAPIView

# DRF routes
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from api import drf_views as api_views
from flash_update import views as flash_views
from per import drf_views as per_views
from deployments import drf_views as deployment_views
from notifications import drf_views as notification_views
from registrations import drf_views as registration_views
from country_plan import drf_views as country_plan_views
from lang import views as lang_views
from dref import views as dref_views


router = routers.DefaultRouter()

router.register(r'action', api_views.ActionViewset, basename='action')
router.register(r'flash-update-action', flash_views.FlashActionViewset, basename='flash_update_action')
router.register(r'appeal', api_views.AppealViewset, basename='appeal')
router.register(r'appeal_document', api_views.AppealDocumentViewset, basename='appeal_document')
router.register(r'country', api_views.CountryViewset, basename='country')
router.register(r'review-country', api_views.CountryOfFieldReportToReviewViewset, basename='review_country')
router.register(r'country_rmd', api_views.CountryRMDViewset, basename='country_rmd')
router.register(r'country_key_figure', api_views.CountryKeyFigureViewset, basename='country_key_figure')
router.register(r'country_snippet', api_views.CountrySnippetViewset, basename='country_snippet')
router.register(r'data-bank/country-overview', CountryOverviewViewSet)
router.register(r'disaster_type', api_views.DisasterTypeViewset, basename='disaster_type')
router.register(r'admin2', api_views.Admin2Viewset, basename='admin2')
router.register(r'district', api_views.DistrictViewset, basename='district')
router.register(r'district_rmd', api_views.DistrictRMDViewset, basename='district_rmd')
router.register(r'domainwhitelist', registration_views.DomainWhitelistViewset)
router.register(r'eru', deployment_views.ERUViewset, basename='eru')
router.register(r'eru_owner', deployment_views.ERUOwnerViewset, basename='eru_owner')
router.register(r'event', api_views.EventViewset, basename='event')
router.register(r'go-historical', api_views.GoHistoricalViewSet, basename='go_historical')
router.register(r'featured_event_deployments', api_views.EventDeploymentsViewset, basename='featured_event_deployments')
router.register(r'field_report', api_views.FieldReportViewset, basename='field_report')
router.register(r'event_snippet', api_views.EventSnippetViewset, basename='event_snippet')
router.register(r'external_partner', api_views.ExternalPartnerViewset, basename='external_partner')
router.register(r'language', lang_views.LanguageViewSet, basename='language')
router.register(r'main_contact', api_views.MainContactViewset, basename='main_contact')
router.register(r'nslinks', api_views.NSLinksViewset, basename='ns_links')
router.register(r'partner_deployment', deployment_views.PartnerDeploymentViewset, basename='partner_deployment')

# PER apis
router.register(r'per-overview', per_views.PerOverviewViewSet, basename='new_per')
router.register(r'per-assessment', per_views.FormAssessmentViewSet, basename='per-assessent')
router.register(r'per-prioritization', per_views.FormPrioritizationViewSet, basename='per-priorirization')
router.register(r'per-work-plan', per_views.NewPerWorkPlanViewSet)
router.register(r'per-formanswer', per_views.FormAnswerViewset, basename='per-formanswer')
router.register(r'per-formarea', per_views.FormAreaViewset, basename='per-formarea')
router.register(r'per-formcomponent', per_views.FormComponentViewset, basename='per-formcomponent')
router.register(r'per-formquestion', per_views.FormQuestionViewset, basename='per-formquestion')
router.register(r'aggregated-per-process-status', per_views.PerAggregatedViewSet, basename='aggregated-per-process-status'),
router.register(r'per-file', per_views.PerFileViewSet, basename='per-file')
router.register(r'per-process-status', per_views.PerProcessStatusViewSet, basename='per-process-status')
router.register(r'perdocs', per_views.PERDocsViewset)
router.register(r'per-country', per_views.PerCountryViewSet, basename='per-country')
router.register(r'latest-per-overview', per_views.LatestCountryOverviewViewset, basename='latest_country_overview')

router.register(r'personnel_deployment', deployment_views.PersonnelDeploymentViewset, basename='personnel_deployment')
router.register(r'personnel', deployment_views.PersonnelViewset, basename='personnel')
router.register(r'personnel_by_event', api_views.DeploymentsByEventViewset, basename='personnel_by_event')
router.register(r'profile', api_views.ProfileViewset, basename='profile')
router.register(r'project', deployment_views.ProjectViewset)
router.register(r'emergency-project', deployment_views.EmergencyProjectViewSet)
router.register(r'region', api_views.RegionViewset, basename='region')
router.register(r'region_key_figure', api_views.RegionKeyFigureViewset, basename='region_key_figure')
router.register(r'region_snippet', api_views.RegionSnippetViewset, basename='region_snippet')
router.register(r'region-project', deployment_views.RegionProjectViewset, basename='region-project')
router.register(r'global-project', deployment_views.GlobalProjectViewset, basename='global-project')
router.register(r'regional-project', deployment_views.RegionalProjectViewset)
router.register(r'supported_activity', api_views.SupportedActivityViewset, basename='supported_activity')
router.register(r'situation_report', api_views.SituationReportViewset, basename='situation_report')
router.register(r'situation_report_type', api_views.SituationReportTypeViewset, basename='situation_report_type')
router.register(r'subscription', notification_views.SubscriptionViewset, basename='subscription')
router.register(r'surge_alert', notification_views.SurgeAlertViewset, basename='surge_alert')
router.register(r'user', api_views.UserViewset, basename='user')
router.register(r'flash-update', flash_views.FlashUpdateViewSet, basename='flash_update')
router.register(r'flash-update-file', flash_views.FlashUpdateFileViewSet, basename='flash_update_file')
router.register(r'donor-group', flash_views.DonorGroupViewSet, basename='donor_group')
router.register(r'donor', flash_views.DonorsViewSet, basename='donor')
router.register(r'share-flash-update', flash_views.ShareFlashUpdateViewSet, basename='share_flash_update')
router.register(r'users', api_views.UsersViewset, basename='users')

# Dref apis
router.register(r"dref", dref_views.DrefViewSet, basename="dref")
router.register(r"dref-files", dref_views.DrefFileViewSet, basename="dref_files")
router.register(r"dref-op-update", dref_views.DrefOperationalUpdateViewSet, basename="dref_operational_update")
router.register(r"dref-final-report", dref_views.DrefFinalReportViewSet, basename="dref_final_report")
router.register(r"completed-dref", dref_views.CompletedDrefOperationsViewSet, basename="completed_dref")
router.register(r"active-dref", dref_views.ActiveDrefOperationsViewSet, basename="active_dref")
router.register(r"dref-share-user", dref_views.DrefShareUserViewSet, basename="dref_share_user")

router.register(r"review-country", api_views.CountryOfFieldReportToReviewViewset, basename="review_country")

# Country Plan apis
router.register(r"country-plan", country_plan_views.CountryPlanViewset, basename="country_plan")

admin.site.site_header = "IFRC Go administration"
admin.site.site_title = "IFRC Go admin"

urlpatterns = [
    url(r"^api/v1/es_search/", EsPageSearch.as_view()),
    url(r"^api/v1/search/", HayStackSearch.as_view()),
    url(r"^api/v1/es_health/", EsPageHealth.as_view()),
    # If we want to use the next one, some fixes needed, e.g.
    # stackoverflow.com/questions/47166385/dont-know-how-to-convert-the-django-field-skills-class-taggit-managers-tagga
    url(r"^api/v1/graphql/", GraphQLView.as_view(graphiql=True)),
    url(r"^api/v1/aggregate/", AggregateByTime.as_view()),
    url(r"^api/v1/aggregate_dtype/", AggregateByDtype.as_view()),
    url(r"^api/v1/aggregate_area/", AreaAggregate.as_view()),
    url(r"^api/v2/appeal/aggregated", AggregateHeaderFigures.as_view()),
    url(r"^api/v2/deployment/aggregated$", deployment_views.AggregateDeployments.as_view()),
    url(r"^api/v2/deployment/aggregated_by_month", deployment_views.DeploymentsByMonth.as_view()),
    url(r"^api/v2/deployment/aggregated_by_ns", deployment_views.DeploymentsByNS.as_view()),
    url(r"^api/v2/brief", Brief.as_view()),
    url(r"^api/v2/erutype", ERUTypes.as_view()),
    url(r"^api/v2/recentaffected", RecentAffecteds.as_view()),
    url(r"^api/v2/fieldreportstatus", FieldReportStatuses.as_view()),
    url(r"^api/v2/programmetype", ProjectProgrammeTypes.as_view()),
    url(r"^api/v2/primarysector", ProjectPrimarySectors.as_view()),
    url(r"^api/v2/secondarysector", ProjectSecondarySectors.as_view()),
    url(r"^api/v2/operationtype", ProjectOperationTypes.as_view()),
    url(r"^api/v2/projectstatus", ProjectStatuses.as_view()),
    url(r"^api/v2/create_field_report/", api_views.CreateFieldReport.as_view()),
    url(r"^api/v2/update_field_report/(?P<pk>\d+)/", api_views.UpdateFieldReport.as_view()),
    url(r"^get_auth_token", GetAuthToken.as_view()),
    url(r"^api/v2/update_subscriptions/", UpdateSubscriptionPreferences.as_view()),
    url(r"^api/v2/add_subscription/", AddSubscription.as_view()),
    url(r"^api/v2/del_subscription/", DelSubscription.as_view()),
    url(r"^api/v2/add_cronjob_log/", AddCronJobLog.as_view()),
    url(r"^api/v2/flash-update-options/", flash_views.FlashUpdateOptions.as_view()),
    url(r"^api/v2/export-flash-update/(?P<pk>\d+)/", flash_views.ExportFlashUpdateView.as_view()),
    url(r"^api/v2/dref-share/", dref_views.DrefShareView.as_view()),
    url(r"^register", RegistrationView.as_view()),
    url(r"^verify_email", VerifyEmail.as_view()),
    url(r"^validate_user", ValidateUser.as_view()),
    url(r"^change_password", registration_views.ChangePasswordView.as_view()),
    url(r"^recover_password", RecoverPassword.as_view()),
    url(r"^show_username", ShowUsername.as_view()),
    url(r"^resend_validation", ResendValidation.as_view()),
    url(r"^api/v2/", include(router.urls)),
    # PER options
    url(r"^api/v2/per-options/", per_views.PerOptionsView.as_view()),

    url(r"^api/v2/event/(?P<pk>\d+)", api_views.EventViewset.as_view({"get": "retrieve"})),
    url(r"^api/v2/event/(?P<slug>[-\w]+)", api_views.EventViewset.as_view({"get": "retrieve"}, lookup_field="slug")),
    url(r"^api/v2/local-unit/(?P<pk>\d+)", LocalUnitDetailAPIView.as_view()),
    url(r"^api/v2/local-unit/", LocalUnitListAPIView.as_view()),
    url(r"^tinymce/", include("tinymce.urls")),
    url(r"^$", RedirectView.as_view(url="/admin")),
    # url(r'^', admin.site.urls),
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/favicon.ico")),
    url(r"^server-error-for-devs", DummyHttpStatusError.as_view()),
    url(r"^exception-error-for-devs", DummyExceptionError.as_view()),
    path("i18n/", include("django.conf.urls.i18n")),
    # Enums
    url(r"^api/v2/global-enums/", api_views.GlobalEnumView.as_view(), name="global_enums"),
    # Docs
    path("docs/", SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path("api-docs/", SpectacularAPIView.as_view(), name='schema'),
    path("api-docs/swagger-ui/", SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = (
        [
            url("__debug__/", include(debug_toolbar.urls)),
            # For django versions before 2.0:
            # url(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns + static.static(
            settings.MEDIA_URL,
            view=xframe_options_exempt(serve),
            document_root=settings.MEDIA_ROOT,
        )
    )

# API With language URL patterns
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    # NOTE: Current language switcher will not work if set to False.
    # TODO: Fix admin panel language switcher before enabling switcher in production
    prefix_default_language=True,
)
