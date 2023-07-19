import json
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.views import View
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models.fields import IntegerField
from django.db.models import Count, Sum, Q, F, Case, When
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from drf_spectacular.utils import extend_schema

from deployments.models import Heop, ERUType, Sector, SectorTag, ProgrammeTypes, OperationTypes, Statuses
from notifications.models import Subscription, SurgeAlert
from notifications.notification import send_notification
from registrations.models import Recovery, Pending
from deployments.models import Project, ERU, Personnel
from flash_update.models import FlashUpdate

from .esconnection import ES_CLIENT
from .models import Appeal, AppealHistory, AppealType, CronJob, Event, FieldReport, Snippet
from .indexes import ES_PAGE_NAME
from .logger import logger
from haystack.query import SearchQuerySet
from api.models import Country, Region, District
from haystack.query import SQ
from .utils import is_user_ifrc
from api.serializers import (
    AggregateHeaderFiguresSerializer,
    SearchSerializer,
    ProjectPrimarySectorsSerializer,
    ProjectSecondarySectorsSerializer
)


def bad_request(message):
    return JsonResponse({"statusCode": 400, "error_message": message}, status=400)


def bad_http_request(header, message):
    return HttpResponse("<h2>%s</h2><p>%s</p>" % (header, message), status=400)


def unauthorized(message="You must be logged in"):
    return JsonResponse({"statusCode": 401, "error_message": message}, status=401)


class UpdateSubscriptionPreferences(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, True)  # deletePrevious
        if len(errors):
            return Response({"status": 400, "data": "Could not create one or more subscription(s), aborting"})
        return Response({"data": "Success"})


class AddSubscription(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # do not delete previous ones, add only 1 subscription
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, False)
        if len(errors):
            return Response({"status": 400, "data": "Could not add subscription, aborting"})
        return Response({"data": "Success"})


class DelSubscription(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors = Subscription.del_user_subscriptions(self.request.user, request.data)
        if len(errors):
            return Response({"status": 400, "data": "Could not remove subscription, aborting"})
        return Response({"data": "Success"})


class EsPageHealth(APIView):
    def get(self, request):
        health = ES_CLIENT.cluster.health()
        return JsonResponse(health)


class EsPageSearch(APIView):
    def get(self, request):
        page_type = request.GET.get("type", None)
        phrase = request.GET.get("keyword", None)
        if phrase is None:
            return bad_request("Must include a `keyword`")
        index = ES_PAGE_NAME
        query = {"multi_match": {"query": phrase, "fields": ["keyword^3", "body", "name"], "operator": "and"}}

        sort = [
            {"date": {"order": "desc", "missing": "_first"}},
            "_score",
        ]

        if page_type is not None:
            query = {"bool": {"filter": {"term": {"type": page_type}}, "must": {"multi_match": query["multi_match"]}}}

        results = ES_CLIENT.search(
            index=index, doc_type="page", body=json.dumps({"query": query, "sort": sort, "from": 0, "size": 10})
        )
        return JsonResponse(results["hits"])


class HayStackSearch(APIView):

    @extend_schema(request=None, responses=SearchSerializer)
    def get(self, request):
        phrase = request.GET.get("keyword", None)
        if phrase is None:
            return bad_request("Must include a `keyword`")

        if phrase:
            phrase = phrase.lower()
            if self.request.user.is_authenticated:
                if is_user_ifrc(self.request.user):
                    project_response = (
                        SearchQuerySet()
                        .models(Project)
                        .filter(SQ(event_name__content=phrase) | SQ(name__content=phrase) | SQ(iso3__contains=phrase))
                        .order_by("-_score")
                    )
                    emergency_response = (
                        SearchQuerySet()
                        .models(Event)
                        .filter(SQ(name__content=phrase) | SQ(iso3__content=phrase))
                        .order_by("-_score")
                    )
                    fieldreport_response = (
                        SearchQuerySet()
                        .models(FieldReport)
                        .filter(SQ(name__content=phrase) | SQ(iso3__content=phrase))
                        .order_by("-_score")
                    )
                    surge_deployments = (
                        SearchQuerySet()
                        .models(ERU)
                        .filter(SQ(event_name__content=phrase) | SQ(country__contains=phrase) | SQ(iso3__contains=phrase))
                        .order_by("-_score")
                    )
                    rapid_response_deployments = (
                        SearchQuerySet()
                        .models(Personnel)
                        .filter(
                            SQ(deploying_country_name__contains=phrase)
                            | SQ(deployed_to_country_name__contains=phrase)
                            | SQ(event_name__content=phrase)
                        )
                        .order_by("-_score")
                    )
                    surge_alert_response = (
                        SearchQuerySet()
                        .models(SurgeAlert)
                        .filter(
                            SQ(event_name__content=phrase) | SQ(country_name__contains=phrase) | SQ(iso3__contains=phrase)
                        )
                        .order_by("-_score")
                    )
                else:
                    project_response = (
                        SearchQuerySet()
                        .models(Project)
                        .filter(
                            (SQ(event_name__content=phrase) | SQ(name__content=phrase) | SQ(iso3__contains=phrase))
                            & ~SQ(visibility="IFRC Only")
                        )
                        .order_by("-_score")
                    )
                    emergency_response = (
                        SearchQuerySet()
                        .models(Event)
                        .filter((SQ(name__content=phrase) | SQ(iso3__content=phrase)) & ~SQ(visibility="IFRC Only"))
                        .order_by("-_score")
                    )
                    fieldreport_response = (
                        SearchQuerySet()
                        .models(FieldReport)
                        .filter((SQ(name__content=phrase) | SQ(iso3__content=phrase)) & ~SQ(visibility="IFRC Only"))
                        .order_by("-_score")
                    )
                    surge_deployments = (
                        SearchQuerySet()
                        .models(ERU)
                        .filter(
                            SQ(event_name__content=phrase)
                            | SQ(country__contains=phrase)
                            | SQ(iso3__contains=phrase) & ~SQ(visibility="IFRC Only")
                        )
                        .order_by("-_score")
                    )
                    rapid_response_deployments = (
                        SearchQuerySet()
                        .models(Personnel)
                        .filter(
                            (
                                SQ(deploying_country_name__contains=phrase)
                                | SQ(deployed_to_country_name__contains=phrase)
                                | SQ(event_name__content=phrase)
                            )
                            & ~SQ(visibility="IFRC Only")
                        )
                        .order_by("-_score")
                    )
                    surge_alert_response = (
                        SearchQuerySet()
                        .models(SurgeAlert)
                        .filter(
                            (SQ(event_name__content=phrase) | SQ(country_name__contains=phrase) | SQ(iso3__contains=phrase))
                            & ~SQ(visibility="IFRC Only")
                        )
                        .order_by("-_score")
                    )

            else:
                project_response = (
                    SearchQuerySet()
                    .models(Project)
                    .filter(
                        (SQ(event_name__content=phrase) | SQ(name__content=phrase) | SQ(iso3__contains=phrase))
                        & SQ(visibility="Public")
                    )
                    .order_by("-_score")
                )
                emergency_response = (
                    SearchQuerySet()
                    .models(Event)
                    .filter((SQ(name__content=phrase) | SQ(iso3__content=phrase)) & SQ(visibility="Public"))
                    .order_by("-_score")
                )
                fieldreport_response = (
                    SearchQuerySet()
                    .models(FieldReport)
                    .filter((SQ(name__content=phrase) | SQ(iso3__content=phrase)) & SQ(visibility="Public"))
                    .order_by("-_score")
                )
                surge_deployments = (
                    SearchQuerySet()
                    .models(ERU)
                    .filter(
                        SQ(event_name__content=phrase)
                        | SQ(country__contains=phrase)
                        | SQ(iso3__contains=phrase) & SQ(visibility="Public")
                    )
                    .order_by("-_score")
                )
                rapid_response_deployments = (
                    SearchQuerySet()
                    .models(Personnel)
                    .filter(
                        (
                            SQ(deploying_country_name__contains=phrase)
                            | SQ(deployed_to_country_name__contains=phrase)
                            | SQ(event_name__content=phrase)
                        )
                        & SQ(visibility="Public")
                    )
                    .order_by("-_score")
                )
                surge_alert_response = (
                    SearchQuerySet()
                    .models(SurgeAlert)
                    .filter(
                        (SQ(event_name__content=phrase) | SQ(country_name__contains=phrase) | SQ(iso3__contains=phrase))
                        & SQ(visibility="Public")
                    )
                    .order_by("-_score")
                )

            region_response = SearchQuerySet().models(Region).filter(SQ(name__startswith=phrase))
            country_response = (
                SearchQuerySet()
                .models(Country)
                .filter(SQ(name__contains=phrase, independent="true", is_depercent="false") | SQ(iso3__contains=phrase))
                .order_by("-_score")
            )
            # appeal_response = SearchQuerySet().models(Appeal).filter(
            #     SQ(name__content=phrase) | SQ(code__content=phrase) | SQ(iso3__content=phrase)
            # ).order_by('-_score')

            district_province_response = (
                SearchQuerySet()
                .models(District)
                .filter(SQ(name__contains=phrase) | SQ(iso3__contains=phrase))
                .order_by("-_score")
            )
            flash_update_response = (
                SearchQuerySet()
                .models(FlashUpdate)
                .filter(SQ(name__contains=phrase) | SQ(iso3__contains=phrase))
                .order_by("-_score")
            )
            # dref_response = SearchQuerySet().models(Dref).filter(
            #     SQ(name__contains=phrase) | SQ(code__contains=phrase) | SQ(iso3__contains=phrase)
            # ).order_by('-_score')
            # dref_operational_update_response = SearchQuerySet().models(DrefOperationalUpdate).filter(
            #     SQ(name__contains=phrase) | SQ(code__contains=phrase) | SQ(iso3__contains=phrase)
            # ).order_by('-_score')

            # appeals_list = []
            # dref = [
            #     {
            #         "id": int(data.id.split(".")[-1]),
            #         "name": data.name,
            #         "created_at": data.created_at,
            #         "type": "Dref",
            #         "score": data.score,
            #         "country_name": data.country_name,
            #         "country_id": data.country_id,
            #         "code": data.code
            #     } for data in dref_response
            # ]
            # appeals_list.extend(dref)
            # dref_op = [
            #     {
            #         "id": int(data.id.split(".")[-1]),
            #         "name": data.name,
            #         "created_at": data.created_at,
            #         "type": "Operational Update",
            #         "score": data.score,
            #         "country_name": data.country_name,
            #         "country_id": data.country_id,
            #         "code": data.code
            #     } for data in dref_operational_update_response
            # ]
            # appeals_list.extend(dref_op)
            # appeal_data = [
            #     {
            #         "id": int(data.id.split(".")[-1]),
            #         "name": data.name,
            #         "code": data.code,
            #         "country": data.country_name,
            #         "country_id": data.country_id,
            #         "start_date": data.start_date,
            #         "score": data.score,
            #         "type": "Appeal",
            #     } for data in appeal_response
            # ]
            # appeals_list.extend(appeal_data)
            field_report = []
            flash_update = [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "created_at": data.created_at,
                    "type": "Flash Update",
                    "score": data.score,
                }
                for data in flash_update_response
            ]
            field_report.extend(flash_update)
            field_reports_data = [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "created_at": data.created_at,
                    "type": "Field Report",
                    "score": data.score,
                }
                for data in fieldreport_response.order_by("-created_at")
            ]
            field_report.extend(field_reports_data)
        result = {
            "regions": [
                {"id": int(data.id.split(".")[-1]), "name": data.name, "score": data.score} for data in region_response[:50]
            ],
            "district_province_response": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "score": data.score,
                    "country": data.country_name,
                    "country_id": data.country_id,
                }
                for data in district_province_response[:50]
            ],
            "countries": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "society_name": data.society_name,
                    "iso3": data.iso3,
                    "score": data.score,
                }
                for data in country_response[:50]
            ],
            "emergencies": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "disaster_type": data.disaster_type,
                    "funding_requirements": data.amount_requested,
                    "funding_coverage": data.amount_funded,
                    "start_date": data.disaster_start_date,
                    "score": data.score,
                    "countries": Country.objects.filter(id__in=data.countries_id),
                    # "iso3": data.iso3,
                    "severity_level_display": data.crisis_categorization,
                    "appeal_type": data.appeal_type,
                    "severity_level": data.severity_level,
                }
                for data in emergency_response[:50]
            ],
            "surge_alerts": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "keywords": data.molnix_tag,
                    "event_name": data.event_name,
                    "country": data.country_name,
                    "start_date": data.start_date,
                    "alert_date": data.alert_date,
                    "score": data.score,
                    "event_id": data.event_id,
                    "status": data.status,
                    "deadline": data.deadline,
                    "surge_type": data.surge_type,
                    "country_id": data.country_id,
                }
                for data in surge_alert_response.order_by("-start_date")[:50]
            ],
            "projects": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name,
                    "event_name": data.event_name,
                    "national_society": data.reporting_ns,
                    "tags": data.tags,
                    "sector": data.sector,
                    "start_date": data.start_date,
                    "end_date": data.end_date,
                    "regions": data.project_districts,
                    "people_targeted": data.target_total,
                    "score": data.score,
                    "event_id": data.event_id,
                    "national_society_id": data.reporting_ns_id,
                }
                for data in project_response.order_by("-start_date")[:50]
            ],
            "surge_deployments": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "event_name": data.event_name,
                    "deployed_country": data.country,
                    "type": data.eru_type,
                    "owner": data.eru_owner,
                    "personnel_units": data.personnel_units,
                    "equipment_units": data.equipment_units,
                    "event_id": data.event_id,
                    "score": data.score,
                    "deployed_country_id": data.country_id,
                    "deployed_country_name": data.country_name,
                }
                for data in surge_deployments[:50]
            ],
            "reports": sorted(field_report, key=lambda d: d["score"], reverse=True)[:50],
            # "emergency_planning": sorted(appeals_list, key=lambda d: d["score"], reverse=True)[:50],
            "rapid_response_deployments": [
                {
                    "id": int(data.id.split(".")[-1]),
                    "name": data.name if self.request.user.is_authenticated else None,
                    "start_date": data.start_date,
                    "end_date": data.end_date,
                    "postion": data.postion,
                    "type": data.type,
                    "deploying_country_name": data.deploying_country_name,
                    "deploying_country_id": data.deploying_country_id,
                    "deployed_to_country_name": data.deployed_to_country_name,
                    "deployed_to_country_id": data.deployed_to_country_id,
                    "event_name": data.event_name,
                    "event_id": data.event_id,
                    "score": data.score,
                }
                for data in rapid_response_deployments[:50]
            ],
        }
        return Response(SearchSerializer(result).data)


class Brief(APIView):
    @classmethod
    def get(cls, request):
        e = Event.objects.filter(summary__contains="base64").count()
        s = Snippet.objects.filter(snippet__contains="base64").count()
        r = FieldReport.objects.filter(description__contains="base64").count()
        u = FlashUpdate.objects.filter(situational_overview__contains="base64").count()
        c = CronJob.objects.filter(status=2).count()
        f = Event.objects.filter(disaster_start_date__gt=timezone.now()).count()

        res = ES_CLIENT.cluster.health()
        res["--------------------------------"] = "----------"
        res["base64_img"] = e + s + r + u
        res["events_in_future"] = f
        res["cronjob_err"] = c
        res["maintenance_mode"] = settings.DJANGO_READ_ONLY
        res["git_last_tag"] = settings.LAST_GIT_TAG
        res["git_last_commit"] = settings.SENTRY_CONFIG["release"][0:8]
        return JsonResponse(res, safe=False)


class ERUTypes(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in ERUType.choices]
        return JsonResponse(keys_labels, safe=False)


class FieldReportStatuses(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in FieldReport.Status.choices]
        return JsonResponse(keys_labels, safe=False)


class RecentAffecteds(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in FieldReport.RecentAffected.choices]
        return JsonResponse(keys_labels, safe=False)


class ProjectProgrammeTypes(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in ProgrammeTypes.choices]
        return JsonResponse(keys_labels, safe=False)


class ProjectPrimarySectors(APIView):
    @classmethod
    @extend_schema(
        request=None,
        responses=ProjectPrimarySectorsSerializer(many=True),
    )
    def get(cls, request):
        keys_labels = [
            {"key": s.id, "label": s.title, "color": s.color, "is_deprecated": s.is_deprecated} for s in Sector.objects.all()
        ]
        return Response(
            ProjectPrimarySectorsSerializer(keys_labels, many=True).data
        )


class ProjectSecondarySectors(APIView):
    @classmethod
    @extend_schema(
        request=None,
        responses=ProjectSecondarySectorsSerializer(many=True),
    )
    def get(cls, request):
        keys_labels = [
            {"key": s.id, "label": s.title, "color": s.color, "is_deprecated": s.is_deprecated}
            for s in SectorTag.objects.all()
        ]
        return Response(
            ProjectSecondarySectorsSerializer(keys_labels, many=True).data
        )


class ProjectOperationTypes(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in OperationTypes.choices]
        return JsonResponse(keys_labels, safe=False)


class ProjectStatuses(APIView):
    @classmethod
    def get(cls, request):
        keys_labels = [{"key": i, "label": v} for i, v in Statuses.choices]
        return JsonResponse(keys_labels, safe=False)


class AggregateHeaderFigures(APIView):
    """
        Used mainly for the key-figures header and by FDRS
    """
    @extend_schema(request=None, responses=AggregateHeaderFiguresSerializer)
    def get(self, request):
        iso3 = request.GET.get("iso3", None)
        country = request.GET.get("country", None)
        region = request.GET.get("region", None)

        now = timezone.now()
        date = request.GET.get("date", now)
        appeal_conditions = (
            (Q(atype=AppealType.APPEAL) | Q(atype=AppealType.INTL)) & Q(end_date__gt=date) & Q(start_date__lt=date)
        )

        all_appealhistory = AppealHistory.objects.select_related("appeal").filter(
            valid_from__lt=date, valid_to__gt=date, appeal__code__isnull=False
        )

        if iso3:
            all_appealhistory = all_appealhistory.filter(country__iso3__iexact=iso3)
        if country:
            all_appealhistory = all_appealhistory.filter(country__id=country)
        if region:
            all_appealhistory = all_appealhistory.filter(country__region__id=region)

        appeals_aggregated = all_appealhistory.annotate(
            # Active Appeals with DREF type
            actd=Count(
                Case(
                    When(Q(atype=AppealType.DREF) & Q(end_date__gt=date) & Q(start_date__lt=date), then=1),
                    output_field=IntegerField(),
                )
            ),
            # Active Appeals with type Emergency Appeal or International Appeal
            acta=Count(Case(When(appeal_conditions, then=1), output_field=IntegerField())),
            # Total Appeals count which are not DREF
            tota=Count(
                Case(When(Q(atype=AppealType.APPEAL) | Q(atype=AppealType.INTL), then=1), output_field=IntegerField())
            ),
            # Active Appeals' target population
            tarp=Sum(
                Case(
                    When(Q(end_date__gt=date) & Q(start_date__lt=date), then=F("num_beneficiaries")),
                    output_field=IntegerField(),
                )
            ),
            # Active Appeals' requested amount, which are not DREF
            amor=Case(When(appeal_conditions, then=F("amount_requested")), output_field=IntegerField()),
            amordref=Case(
                When(Q(end_date__gt=date) & Q(start_date__lt=date), then=F("amount_requested")), output_field=IntegerField()
            ),
            # Active Appeals' funded amount, which are not DREF
            amof=Case(When(appeal_conditions, then=F("amount_funded")), output_field=IntegerField()),
        ).aggregate(
            active_drefs=Sum("actd"),
            active_appeals=Sum("acta"),
            total_appeals=Sum("tota"),
            target_population=Sum("tarp"),
            amount_requested=Sum("amor"),
            amount_requested_dref_included=Sum("amordref"),
            amount_funded=Sum("amof"),
        )

        return Response(
            AggregateHeaderFiguresSerializer(
                appeals_aggregated
            ).data
        )


class AreaAggregate(APIView):
    def get(self, request):
        region_type = request.GET.get("type", None)
        region_id = request.GET.get("id", None)

        if region_type not in ["country", "region"]:
            return bad_request("`type` must be `country` or `region`")
        elif not region_id:
            return bad_request("`id` must be a region id")

        aggregate = (
            Appeal.objects.filter(**{region_type: region_id})
            .annotate(count=Count("id"))
            .aggregate(Sum("num_beneficiaries"), Sum("amount_requested"), Sum("amount_funded"), Sum("count"))
        )

        return JsonResponse(dict(aggregate))


class AggregateByDtype(APIView):
    def get(self, request):
        models = {
            "appeal": Appeal,
            "event": Event,
            "fieldreport": FieldReport,
            "heop": Heop,
        }
        mtype = request.GET.get("model_type", None)
        if mtype is None or mtype not in models:
            return bad_request("Must specify an `model_type` that is `heop`, `appeal`, `event`, or `fieldreport`")

        model = models[mtype]
        aggregate = model.objects.values("dtype").annotate(count=Count("id")).order_by("count").values("dtype", "count")

        return JsonResponse(dict(aggregate=list(aggregate)))


class AggregateByTime(APIView):
    def get(self, request):
        models = {
            "appeal": Appeal,
            "event": Event,
            "fieldreport": FieldReport,
            "heop": Heop,
        }

        unit = request.GET.get("unit", None)
        start_date = request.GET.get("start_date", None)
        mtype = request.GET.get("model_type", None)

        country = request.GET.get("country", None)
        region = request.GET.get("region", None)

        if mtype is None or mtype not in models:
            return bad_request("Must specify an `model_type` that is `heop`, `appeal`, `event`, or `fieldreport`")

        if start_date is None:
            start_date = datetime(1980, 1, 1, tzinfo=timezone.utc)
        else:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return bad_request("`start_date` must be YYYY-MM-DD format")

            start_date = start_date.replace(tzinfo=timezone.utc)

        model = models[mtype]

        # set date filter property
        date_filter = "created_at"
        if mtype == "appeal" or mtype == "heop":
            date_filter = "start_date"
        elif mtype == "event":
            date_filter = "disaster_start_date"

        filter_obj = {date_filter + "__gte": start_date}

        # useful shortcut for singular/plural location filters
        is_appeal = True if mtype == "appeal" else False

        # set country and region filter properties
        if country is not None:
            country_filter = "country" if is_appeal else "countries__in"
            countries = country if is_appeal else [country]
            filter_obj[country_filter] = countries
        elif region is not None:
            region_filter = "region" if is_appeal else "regions__in"
            regions = region if is_appeal else [region]
            filter_obj[region_filter] = regions

        # allow custom filter attributes
        # TODO this should check if the model definition contains this field
        for key, value in request.GET.items():
            if key[0:7] == "filter_":
                filter_obj[key[7:]] = value

        # allow arbitrary SUM functions
        annotation_funcs = {"count": Count("id")}
        output_values = ["timespan", "count"]
        for key, value in request.GET.items():
            if key[0:4] == "sum_":
                annotation_funcs[key[4:]] = Sum(value)
                output_values.append(key[4:])

        trunc_method = TruncMonth if unit == "month" else TruncYear

        aggregate = (
            model.objects.filter(**filter_obj)
            .annotate(timespan=trunc_method(date_filter, tzinfo=timezone.utc))
            .values("timespan")
            .annotate(**annotation_funcs)
            .order_by("timespan")
            .values(*output_values)
        )

        return JsonResponse(dict(aggregate=list(aggregate)))


class GetAuthToken(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)

        if "ifrc" in password.lower() or "redcross" in password.lower():
            logger.warning("User should be warned to use a stronger password.")

        if username is None or password is None:
            logger.error("Should not happen. Frontend prevents login without username/password")
            return bad_request("Body must contain `email/username` and `password`")

        user = authenticate(username=username, password=password)
        if user == None and User.objects.filter(email=username).count() > 1:
            users = User.objects.filter(email=username, is_active=True)
            if users:
                # We get the first one if there are still multiple available is_active:
                user = authenticate(username=users[0].username, password=password)

        # Determining the client IP is not always straightforward:
        clientIP = ""
        # if 'REMOTE_ADDR' in request.META:        clientIP += 'R' + request.META['REMOTE_ADDR']
        # if 'HTTP_CLIENT_IP' in request.META:     clientIP += 'C' + request.META['HTTP_CLIENT_IP']
        # if 'HTTP_X_FORWARDED' in request.META:   clientIP += 'x' + request.META['HTTP_X_FORWARDED']
        # if 'HTTP_FORWARDED_FOR' in request.META: clientIP += 'F' + request.META['HTTP_FORWARDED_FOR']
        # if 'HTTP_FORWARDED' in request.META:     clientIP += 'f' + request.META['HTTP_FORWARDED']
        if "HTTP_X_FORWARDED_FOR" in request.META:
            clientIP += request.META["HTTP_X_FORWARDED_FOR"].split(",")[0]

        logger.info(
            "%s FROM %s: %s (%s) %s"
            % (
                username,
                clientIP,
                "ok" if user else "ERR",
                request.META["HTTP_ACCEPT_LANGUAGE"] if "HTTP_ACCEPT_LANGUAGE" in request.META else "",
                request.META["HTTP_USER_AGENT"] if "HTTP_USER_AGENT" in request.META else "",
            )
        )

        if user is not None:
            api_key, created = Token.objects.get_or_create(user=user)

            # Reset the key's created_at time each time we get new credentials
            if not created:
                api_key.created = timezone.now()
                api_key.save()

            # (Re)set the user's last frontend login datetime
            user.profile.last_frontend_login = timezone.now()
            user.profile.save()

            return JsonResponse(
                {
                    "token": api_key.key,
                    "username": username,
                    "first": user.first_name,
                    "last": user.last_name,
                    "expires": api_key.created + timedelta(7),
                    "id": user.id,
                }
            )
        else:
            return bad_request("Invalid username or password")  # most probably password issue


class ChangePassword(APIView):
    permissions_classes = []

    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        new_pass = request.data.get("new_password", None)
        token = request.data.get("token", None)
        # 'password' is checked for Change Password, 'token' is checked for Password Recovery
        if username is None or (password is None and token is None):
            return bad_request("Must include a `username` and either a `password` or `token`")

        if new_pass is None:
            return bad_request("Must include a `new_password` property")
        try:
            validate_password(new_pass)
        except Exception as exc:
            ers = " ".join(str(err) for err in exc)
            return bad_request(ers)

        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            return bad_request("Could not authenticate")

        if password and not user.check_password(password):
            return bad_request("Could not authenticate")
        elif token:
            recovery = Recovery.objects.filter(user=user).first()
            if recovery is None:
                return bad_request("Could not authenticate")

            if recovery.token != token:
                return bad_request("Could not authenticate")
            recovery.delete()

        user.set_password(new_pass)
        user.save()

        return JsonResponse({"status": "ok"})


class RecoverPassword(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", None)
        if email is None:
            return bad_request("Must include an `email` property")

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return bad_request("That email is not associated with a user")

        token = get_random_string(length=32)
        Recovery.objects.filter(user=user).delete()
        Recovery.objects.create(user=user, token=token)
        email_context = {"frontend_url": settings.FRONTEND_URL, "username": user.username, "token": token}
        send_notification(
            "Reset your password",
            [user.email],
            render_to_string("email/recover_password.html", email_context),
            "Password recovery - " + user.username,
        )

        return JsonResponse({"status": "ok"})


class ShowUsername(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", None)
        if email is None:
            return bad_request("Must include an `email` property")

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return bad_request("That email is not associated with a user")

        email_context = {
            "username": user.username,
        }
        send_notification(
            "Showing your username",
            [user.email],
            render_to_string("email/show_username.html", email_context),
            "Username recovery - " + user.username,
        )

        return JsonResponse({"status": "ok"})


class ResendValidation(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get("username", None)

        if username:
            # Now we allow requesting with either email or username
            pending_user = (
                Pending.objects.select_related("user")
                .filter(Q(user__username__iexact=username) | Q(user__email__iexact=username))
                .first()
            )
            if pending_user:
                if pending_user.user.is_active is True:
                    return bad_request(
                        "Your registration is already active, \
                                        you can try logging in with your registered username and password"
                    )
                if pending_user.created_at < timezone.now() - timedelta(days=30):
                    return bad_request(
                        "The verification period is expired. \
                                        You must verify your email within 30 days. \
                                        Please contact your system administrator."
                    )

                # Construct and re-send the email
                email_context = {
                    "confirmation_link": "https://%s/verify_email/?token=%s&user=%s"
                    % (
                        settings.BASE_URL,  # on PROD it should point to goadmin...
                        pending_user.token,
                        username,
                    )
                }

                if pending_user.user.is_staff:
                    template = "email/registration/verify-staff-email.html"
                else:
                    template = "email/registration/verify-outside-email.html"

                send_notification(
                    "Validate your account",
                    [pending_user.user.email],
                    render_to_string(template, email_context),
                    "Validate account - " + username,
                )
                return Response({"data": "Success"})
            else:
                return bad_request(
                    "No pending registration found with the provided username. \
                                    Please check your input."
                )
        else:
            return bad_request("Please provide your username in the request.")


class AddCronJobLog(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors, created = CronJob.sync_cron(request.data)
        if len(errors):
            return Response({"status": 400, "data": "Could not add CronJob, aborting"})
        return Response({"data": "Success"})


class DummyHttpStatusError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=500)


class DummyExceptionError(View):
    def get(self, request, *args, **kwargs):
        raise Exception("Dev raised exception!")
