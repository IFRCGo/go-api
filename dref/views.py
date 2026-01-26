import csv

import django.utils.timezone as timezone
from django.contrib.auth.models import Permission
from django.db import models, transaction
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils.translation import gettext
from drf_spectacular.utils import extend_schema
from rest_framework import (
    mixins,
    permissions,
    response,
    serializers,
    status,
    views,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from reversion.views import RevisionMixin

from api.models import AppealFilter
from api.utils import get_model_name
from dref.filter_set import (
    ActiveDrefFilterSet,
    CompletedDrefOperationsFilterSet,
    DrefFilter,
    DrefOperationalUpdateFilter,
    DrefShareUserFilterSet,
)
from dref.models import Dref, DrefFile, DrefFinalReport, DrefOperationalUpdate
from dref.permissions import ApproveDrefPermission
from dref.serializers import (
    AddDrefUserSerializer,
    CompletedDrefOperationsSerializer,
    Dref3Serializer,
    DrefFileInputSerializer,
    DrefFileSerializer,
    DrefFinalReport3Serializer,
    DrefFinalReportSerializer,
    DrefGlobalFilesSerializer,
    DrefOperationalUpdate3Serializer,
    DrefOperationalUpdateSerializer,
    DrefSerializer,
    DrefShareUserSerializer,
    MiniDrefSerializer,
)
from dref.tasks import process_dref_translation
from main.permissions import DenyGuestUserPermission


def filter_dref_queryset_by_user_access(user, queryset):
    if user.is_superuser:
        return queryset
    # Check if regional admin
    dref_admin_regions_id = [
        codename.replace("dref_region_admin_", "")
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="dref_region_admin_",
        ).values_list("codename", flat=True)
    ]
    if len(dref_admin_regions_id):
        return queryset.filter(
            models.Q(created_by=user) | models.Q(country__region__in=dref_admin_regions_id) | models.Q(users=user)
        ).distinct()
    # Normal access
    return queryset.model.get_for(user)


class DrefViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = DrefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Dref.objects.prefetch_related(
                "planned_interventions", "needs_identified", "national_society_actions", "users", "proposed_action"
            )
            .order_by("-created_at")
            .distinct()
        )
        return filter_dref_queryset_by_user_access(user, queryset)

    @extend_schema(request=None, responses=DrefSerializer)
    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, ApproveDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        dref = self.get_object()
        if dref.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("This Dref has already been approved."))
        if dref.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved"))
        dref.status = Dref.Status.APPROVED
        dref.save(update_fields=["status"])
        serializer = DrefSerializer(dref, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=DrefSerializer)
    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        dref = self.get_object()
        if dref.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(gettext("Cannot be finalized because it is already %s") % dref.get_status_display())
        if dref.translation_module_original_language == "en":
            dref.status = Dref.Status.FINALIZED
            dref.save(update_fields=["status"])
            serializer = DrefSerializer(dref, context={"request": request})
            return response.Response(serializer.data)

        model_name = get_model_name(type(dref))
        dref.status = Dref.Status.FINALIZING
        dref.save(update_fields=["status"])
        transaction.on_commit(lambda: process_dref_translation.delay(model_name, dref.pk))
        return response.Response(
            {"detail": gettext("The translation is currently being processed. Please wait a little while before trying again.")},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(request=None, responses=DrefGlobalFilesSerializer)
    @action(
        detail=False,
        url_path="global-files",
        methods=["get"],
        serializer_class=DrefGlobalFilesSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def get_global_files(self, request, pk=None, version=None):
        """
        Dref global files url
        """
        return response.Response(
            DrefGlobalFilesSerializer(
                {"budget_template_url": request.build_absolute_uri(static("files/dref/budget_template.xlsm"))}
            ).data
        )


class DrefOperationalUpdateViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefOperationalUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = DrefOperationalUpdateFilter

    def get_queryset(self):
        user = self.request.user
        queryset = (
            DrefOperationalUpdate.objects.select_related(
                "national_society",
                "national_society",
                "disaster_type",
                "event_map",
                "cover_image",
                "budget_file",
                "assessment_report",
            )
            .prefetch_related(
                "dref",
                "planned_interventions",
                "needs_identified",
                "national_society_actions",
                "users",
                "images",
                "photos",
            )
            .order_by("-created_at")
            .distinct()
        )
        return filter_dref_queryset_by_user_access(user, queryset)

    @extend_schema(request=None, responses=DrefOperationalUpdateSerializer)
    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, ApproveDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        operational_update = self.get_object()

        if operational_update.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("This Operational update has already been approved."))
        if operational_update.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved."))

        operational_update.status = Dref.Status.APPROVED
        operational_update.save(update_fields=["status"])
        serializer = DrefOperationalUpdateSerializer(operational_update, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=DrefOperationalUpdateSerializer)
    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        operational_update = self.get_object()
        if operational_update.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(
                gettext("Cannot be finalized because it is already %s") % operational_update.get_status_display()
            )
        if operational_update.translation_module_original_language == "en":
            operational_update.status = Dref.Status.FINALIZED
            operational_update.save(update_fields=["status"])
            serializer = DrefOperationalUpdateSerializer(operational_update, context={"request": request})
            return response.Response(serializer.data)

        model_name = get_model_name(type(operational_update))
        operational_update.status = Dref.Status.FINALIZING
        operational_update.save(update_fields=["status"])
        transaction.on_commit(lambda: process_dref_translation.delay(model_name, operational_update.pk))
        return response.Response(
            {"detail": gettext("The translation is currently being processed. Please wait a little while before trying again.")},
            status=status.HTTP_202_ACCEPTED,
        )


class DrefFinalReportViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefFinalReportSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = (
            DrefFinalReport.objects.prefetch_related(
                "dref__planned_interventions",
                "dref__needs_identified",
            )
            .order_by("-created_at")
            .distinct()
        )
        return filter_dref_queryset_by_user_access(user, queryset)

    @extend_schema(request=None, responses=DrefFinalReportSerializer)
    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, ApproveDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        final_report = self.get_object()
        if final_report.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("This Final Report has already been approved."))

        if final_report.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved."))

        final_report.status = Dref.Status.APPROVED
        final_report.save(update_fields=["status"])
        final_report.dref.is_active = False
        final_report.date_of_approval = timezone.now().date()
        final_report.dref.save(update_fields=["is_active", "date_of_approval"])
        serializer = DrefFinalReportSerializer(final_report, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=DrefFinalReportSerializer)
    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        final_report = self.get_object()
        if final_report.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(
                gettext("Cannot be finalized because it is already %s") % final_report.get_status_display()
            )
        if final_report.translation_module_original_language == "en":
            final_report.status = Dref.Status.FINALIZED
            final_report.save(update_fields=["status"])
            serializer = DrefFinalReportSerializer(final_report, context={"request": request})
            return response.Response(serializer.data)

        model_name = get_model_name(type(final_report))
        final_report.status = Dref.Status.FINALIZING
        final_report.save(update_fields=["status"])
        transaction.on_commit(lambda: process_dref_translation.delay(model_name, final_report.pk))
        return response.Response(
            {"detail": gettext("The translation is currently being processed. Please wait a little while before trying again.")},
            status=status.HTTP_202_ACCEPTED,
        )


class DrefFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    serializer_class = DrefFileSerializer

    def get_queryset(self):
        if self.request is None:
            return DrefFile.objects.none()
        return DrefFile.objects.filter(created_by=self.request.user)

    @extend_schema(request=DrefFileInputSerializer, responses=DrefFileSerializer(many=True))
    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = [files[0] for files in dict((request.data).lists()).values()]
        data = [{"file": file} for file in files]
        file_serializer = DrefFileSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompletedDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompletedDrefOperationsSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserPermission,
    ]
    filterset_class = CompletedDrefOperationsFilterSet
    queryset = DrefFinalReport.objects.filter(status=Dref.Status.APPROVED).order_by("-created_at").distinct()

    def get_queryset(self):
        user = self.request.user
        return filter_dref_queryset_by_user_access(user, super().get_queryset())


class ActiveDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MiniDrefSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = ActiveDrefFilterSet
    queryset = (
        Dref.objects.prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
        .order_by("-created_at")
        .filter(is_active=True)
        .distinct()
    )

    def get_queryset(self):
        # user = self.request.user
        return filter_dref_queryset_by_user_access(self.request.user, super().get_queryset()).order_by("-created_at")


class DrefShareView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]

    @extend_schema(request=AddDrefUserSerializer, responses=None)
    def post(self, request):
        serializer = AddDrefUserSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(status=status.HTTP_200_OK)


class DrefShareUserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserPermission,
    ]
    serializer_class = DrefShareUserSerializer
    filterset_class = DrefShareUserFilterSet

    def get_queryset(self):
        return (
            Dref.objects.prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("-created_at")
            .distinct()
        )


class Dref3ViewSet(RevisionMixin, viewsets.ModelViewSet):  # type: ignore[misc]
    # Allow unauthenticated access; we'll filter published-only for anonymous users below
    permission_classes = [permissions.AllowAny]
    # Previous: [permissions.IsAuthenticated, DenyGuestUserPermission, UseBySuperAdminOnly]
    lookup_field = "appeal_code"

    def get_queryset(self):  # type: ignore[override]
        # just to give something to rest_framework/generics.py:63 – not used in retrieve
        return Dref.objects.none()

    def get_nonsuperusers_excluded_codes(self):
        """Return a set of appeal_codes that should be hidden from non-superusers.
        Accepts CSV values in AppealFilter.value like "MDRXX019,MDRYY036".
        """
        try:
            if AppealFilter.objects.values_list("value", flat=True).filter(name="ingestAppealFilter").count() > 0:
                codes_exc = AppealFilter.objects.values_list("value", flat=True).filter(name="ingestAppealFilter")[0].split(",")
            else:
                codes_exc = []
        except Exception:
            # If model/app not available, fail open (no extra exclusions)
            return set()
        excluded = set()
        for code in codes_exc:
            c = code.strip().upper()
            if c:
                excluded.add(c)
        return excluded

    def _parse_stage_filter(self, raw):
        """Return canonical stage names (application, operational_update, final_report) from input string.
        Accepts comma-separated values; case-insensitive; supports short forms: app, op, final.
        """
        if not raw:
            return None
        mapping = {
            "application": "application",
            "app": "application",
            "dref": "application",
            "operational_update": "operational_update",
            "operationalupdate": "operational_update",
            "op_update": "operational_update",
            "op": "operational_update",
            "update": "operational_update",
            "final_report": "final_report",
            "finalreport": "final_report",
            "final": "final_report",
            "report": "final_report",
        }
        stages = set()
        for part in str(raw).split(","):
            key = part.strip().lower()
            if key in mapping:
                stages.add(mapping[key])
        return stages or None

    def _status_to_int(self, raw):
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            pass
        label_map = {s.label.lower(): s.value for s in Dref.Status}
        name_map = {s.name.lower(): s.value for s in Dref.Status}
        return label_map.get(str(raw).lower()) or name_map.get(str(raw).lower())

    def list(self, request):
        # === First approach – would be nice to work like this, but recent definitons are more complex than that:
        # # Aggregate all appeal-codes from the three models
        # drefs = Dref.objects.all()
        # ops = DrefOperationalUpdate.objects.all()
        # finals = DrefFinalReport.objects.all()
        # data = Dref3Serializer(list(drefs) + list(ops) + list(finals), many=True).data
        # return response.Response(data)

        # === Second approach:
        # Get appeal_codes – then self.retrieve

        stage_filter = self._parse_stage_filter(request.query_params.get("stage"))
        codes_qs_dref = Dref.objects.exclude(appeal_code="").values_list("appeal_code", flat=True).distinct()
        codes_qs_op = DrefOperationalUpdate.objects.exclude(appeal_code="").values_list("appeal_code", flat=True).distinct()
        codes_qs_final = DrefFinalReport.objects.exclude(appeal_code="").values_list("appeal_code", flat=True).distinct()

        # Filtering by appeal_code prefix
        appeal_code_prefix = request.query_params.get("appeal_code_prefix")
        if appeal_code_prefix:
            codes_qs_dref = codes_qs_dref.filter(appeal_code__startswith=appeal_code_prefix)
            codes_qs_op = codes_qs_op.filter(appeal_code__startswith=appeal_code_prefix)
            codes_qs_final = codes_qs_final.filter(appeal_code__startswith=appeal_code_prefix)

        # region filter
        region_param = request.query_params.get("region")
        if region_param:
            try:
                region_id = int(region_param)
            except ValueError:
                region_id = None
            if region_id:
                codes_qs_dref = codes_qs_dref.filter(national_society__region_id=region_id)
                codes_qs_op = codes_qs_op.filter(national_society__region_id=region_id)
                codes_qs_final = codes_qs_final.filter(national_society__region_id=region_id)

        # country iso3
        iso3_param = request.query_params.get("country_iso3")
        if iso3_param:
            iso3 = iso3_param.strip().upper()
            codes_qs_dref = codes_qs_dref.filter(national_society__iso3__iexact=iso3)
            codes_qs_op = codes_qs_op.filter(national_society__iso3__iexact=iso3)
            codes_qs_final = codes_qs_final.filter(national_society__iso3__iexact=iso3)

        # appeal_type => type_of_dref
        appeal_type_param = request.query_params.get("appeal_type")
        if appeal_type_param:
            try:
                appeal_type_int = int(appeal_type_param)
                codes_qs_dref = codes_qs_dref.filter(type_of_dref=appeal_type_int)
                codes_qs_op = codes_qs_op.filter(dref__type_of_dref=appeal_type_int)
                codes_qs_final = codes_qs_final.filter(dref__type_of_dref=appeal_type_int)
            except ValueError:
                pass

        # operation_status => status
        op_status_int = self._status_to_int(request.query_params.get("operation_status"))
        if op_status_int is not None:
            codes_qs_dref = codes_qs_dref.filter(status=op_status_int)
            codes_qs_op = codes_qs_op.filter(status=op_status_int)
            codes_qs_final = codes_qs_final.filter(status=op_status_int)

        # start/end date of operation
        start_date_param = request.query_params.get("start_date_of_operation")
        if start_date_param:
            # Dref has no operation_start_date; approximate with date_of_approval for application stage records.
            codes_qs_dref = codes_qs_dref.filter(date_of_approval__gte=start_date_param)
            codes_qs_op = codes_qs_op.filter(new_operational_start_date__gte=start_date_param)
            codes_qs_final = codes_qs_final.filter(operation_start_date__gte=start_date_param)
        end_date_param = request.query_params.get("end_date_of_operation")
        if end_date_param:
            codes_qs_dref = codes_qs_dref.filter(end_date__lte=end_date_param)
            codes_qs_op = codes_qs_op.filter(new_operational_end_date__lte=end_date_param)
            codes_qs_final = codes_qs_final.filter(operation_end_date__lte=end_date_param)

        # appeal_id direct (DB primary key)
        appeal_id_param = request.query_params.get("appeal_id")
        if appeal_id_param:
            try:
                pk_val = int(appeal_id_param)
            except ValueError:
                pk_val = None
            codes = []
            if pk_val:
                for model in (Dref, DrefOperationalUpdate, DrefFinalReport):
                    obj = model.objects.filter(pk=pk_val).only("appeal_code").first()
                    if obj and obj.appeal_code:
                        codes = [obj.appeal_code]
                        break
        else:
            codes_sets = []
            if not stage_filter or "application" in stage_filter:
                codes_sets.append(set(codes_qs_dref))
            if not stage_filter or "operational_update" in stage_filter:
                codes_sets.append(set(codes_qs_op))
            if not stage_filter or "final_report" in stage_filter:
                codes_sets.append(set(codes_qs_final))
            combined = set()
            for s in codes_sets:
                combined.update([c for c in s if c])
            codes = sorted(combined)

        # Additional date range filters (applied to root Dref only where fields exist)
        date_range_fields = [
            "event_date",
            "ns_respond_date",
            "government_requested_assistance_date",
            "ns_request_date",
            "submission_to_geneva",
            "date_of_approval",
            "publishing_date",
            "hazard_date_and_location",
            "end_date",
        ]
        for field in date_range_fields:
            from_param = request.query_params.get(f"{field}_from")
            to_param = request.query_params.get(f"{field}_to")
            if from_param:
                codes_qs_dref = codes_qs_dref.filter(**{f"{field}__gte": from_param})
            if to_param:
                codes_qs_dref = codes_qs_dref.filter(**{f"{field}__lte": to_param})

        # Exclude codes for non-superusers
        if not getattr(self.request.user, "is_superuser", False):
            excluded_codes = self.get_nonsuperusers_excluded_codes()
            if excluded_codes:
                codes = [c for c in codes if c and c.upper() not in excluded_codes]

        data = []
        old_kwargs = getattr(self, "kwargs", {}).copy()
        for code in codes:
            self.kwargs = {self.lookup_field: code}
            try:
                resp = self.retrieve(request)
            except NotFound:
                # Skip codes that have no visible records for this user
                continue
            if resp.status_code == 200:
                for item in resp.data if isinstance(resp.data, list) else [resp.data]:
                    if stage_filter:
                        stage_val = None
                        if isinstance(item, dict):
                            stage_val = item.get("stage") or item.get("Stage")
                        if stage_val:
                            normalized_stage = stage_val.lower()
                            if normalized_stage.startswith("operational update"):
                                normalized_stage = "operational_update"
                            elif normalized_stage == "final report":
                                normalized_stage = "final_report"
                            elif normalized_stage == "application":
                                normalized_stage = "application"
                            if normalized_stage not in stage_filter:
                                continue
                        else:
                            # If stage filter present and we cannot determine stage, skip
                            continue
                    data.append(item)
        self.kwargs = old_kwargs  # Restore old kwargs

        # Assign ephemeral numeric ids (1-based sequence) per request and silent_operation flag
        silents = self.get_nonsuperusers_excluded_codes()
        for idx, row in enumerate(data, start=1):
            row["id"] = idx
            row["public"] = row["appeal_id"] not in silents

        # numeric id filter (?id=3 or ?id=3,7)
        id_param = request.query_params.get("id")
        if id_param:
            wanted_ids = {i.strip() for i in str(id_param).split(",") if i.strip().isdigit()}
            if wanted_ids:
                wanted_ints = {int(i) for i in wanted_ids}
                data = [row for row in data if row.get("id") in wanted_ints]
        # pagination
        try:
            limit = int(request.query_params.get("limit")) if request.query_params.get("limit") else None
        except ValueError:
            limit = None
        try:
            offset = int(request.query_params.get("offset")) if request.query_params.get("offset") else 0
        except ValueError:
            offset = 0
        if offset or limit is not None:
            end = offset + limit if limit is not None else None
            data_paginated = data[offset:end]
        else:
            data_paginated = data

        export_param = request.query_params.get("export")
        if export_param and export_param.lower() == "csv":
            header = []
            seen = set()
            for row in data_paginated:
                for k in row.keys():
                    if k not in seen:
                        seen.add(k)
                        header.append(k)
            resp = HttpResponse(content_type="text/csv")
            resp["Content-Disposition"] = 'attachment; filename="dref3_export.csv"'
            writer = csv.writer(resp)
            writer.writerow(header)
            for row in data_paginated:
                writer.writerow([row.get(k, "") for k in header])
            return resp

        return response.Response(data_paginated)

    def get_serializer_class(self):  # type: ignore[override]
        # just to give something to rest_framework/generics.py:122 – not used in retrieve
        return Dref3Serializer

    #    def get_renderers(self):
    #        return [renderer() for renderer in tuple(api_settings.DEFAULT_RENDERER_CLASSES)]

    def get_objects_by_appeal_code(self, appeal_code):
        results = []
        user = self.request.user

        if not getattr(user, "is_superuser", False):
            # If code is in the excluded list, return no results for anonymous users
            excluded_codes = self.get_nonsuperusers_excluded_codes()
            if appeal_code and appeal_code.upper() in excluded_codes:
                return []
            # Light users: only published records are visible
            drefs = (
                Dref.objects.filter(appeal_code=appeal_code, status=Dref.Status.APPROVED)
                .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
                .order_by("created_at")
                .distinct()
            )
            if drefs.exists():
                results.extend(drefs)

            operational_updates = (
                DrefOperationalUpdate.objects.filter(appeal_code=appeal_code, status=Dref.Status.APPROVED)
                .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
                .order_by("created_at")
                .distinct()
            )
            if operational_updates.exists():
                results.extend(operational_updates)

            final_reports = (
                DrefFinalReport.objects.filter(appeal_code=appeal_code, status=Dref.Status.APPROVED)
                .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
                .order_by("created_at")
                .distinct()
            )
            if final_reports.exists():
                results.extend(final_reports)
            return results

        # Strong users: allow more access
        drefs = (
            Dref.objects.filter(appeal_code=appeal_code)
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("created_at")
            .distinct()
        )
        drefs = filter_dref_queryset_by_user_access(user, drefs)
        if drefs.exists():
            results.extend(drefs)

        operational_updates = (
            DrefOperationalUpdate.objects.filter(appeal_code=appeal_code)
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("created_at")
            .distinct()
        )
        operational_updates = filter_dref_queryset_by_user_access(user, operational_updates)
        if operational_updates.exists():
            results.extend(operational_updates)

        final_reports = (
            DrefFinalReport.objects.filter(appeal_code=appeal_code)
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("created_at")
            .distinct()
        )
        final_reports = filter_dref_queryset_by_user_access(user, final_reports)
        if final_reports.exists():
            results.extend(final_reports)
        return results

    def retrieve(self, request, *args, **kwargs):
        code = self.kwargs.get(self.lookup_field)
        instances = self.get_objects_by_appeal_code(code)

        if not instances:
            raise NotFound(f"No Dref, Operational Update, or Final Report found with code '{code}'.")

        serialized_data = []
        ops_update_count = 0
        allocation_count = 1  # Dref Application is always the first allocation
        public = code not in self.get_nonsuperusers_excluded_codes()
        a = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]

        # is_latest_stage: the last APPROVED-status instance and next instance either absent or not APPROVED
        latest_index = None
        for i, inst in enumerate(instances):
            if getattr(inst, "status", None) == Dref.Status.APPROVED:
                next_inst = instances[i + 1] if i + 1 < len(instances) else None
                if next_inst is None or getattr(next_inst, "status", None) != Dref.Status.APPROVED:
                    latest_index = i
        # Build serialized rows with flag
        for i, instance in enumerate(instances):
            is_latest_stage = i == latest_index
            if isinstance(instance, Dref):
                serializer = Dref3Serializer(
                    instance,
                    context={
                        "stage": "Application",
                        "allocation": a[0],
                        "public": public,
                        "is_latest_stage": is_latest_stage,
                    },
                )
            elif isinstance(instance, DrefOperationalUpdate):
                ops_update_count += 1
                if instance.additional_allocation and len(a) > allocation_count:
                    allocation = a[allocation_count]
                    allocation_count += 1
                else:
                    allocation = "No allocation"
                serializer = DrefOperationalUpdate3Serializer(
                    instance,
                    context={
                        "stage": f"Operational Update {ops_update_count}",
                        "allocation": allocation,
                        "public": public,
                        "is_latest_stage": is_latest_stage,
                    },
                )
            elif isinstance(instance, DrefFinalReport):
                serializer = DrefFinalReport3Serializer(
                    instance,
                    context={
                        "stage": "Final Report",
                        "allocation": "No allocation",
                        "public": public,
                        "is_latest_stage": is_latest_stage,
                    },
                )
            else:
                continue
            serialized_data.append(serializer.data)

        return response.Response(serialized_data)

    def get_renderer_context(self):
        context = super().get_renderer_context()
        context["header"] = Dref3Serializer.Meta.fields
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "HEAD"):
            return super().dispatch(request, *args, **kwargs)
        return response.Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
