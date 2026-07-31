import logging

import django.utils.timezone as timezone
from django.contrib.auth.models import Permission
from django.contrib.gis.db.models import Count, Exists, OuterRef, Q
from django.db import models, transaction
from django.db.models.query import Prefetch
from django.templatetags.static import static
from django.utils.translation import gettext
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from reversion.views import RevisionMixin

from api.utils import get_model_name
from dref.dref3.common import (
    DREF3_CSV_CHUNK_SIZE,
    Dref3AccessFilter,
    Dref3PageHydrator,
    EmptyResult,
    dref3_csv_streaming_response,
)
from dref.dref3.query import build_union_queryset, empty_union_queryset
from dref.dref3.serializers import Dref3Serializer
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
    DrefFileInputSerializer,
    DrefFileSerializer,
    DrefFinalReportSerializer,
    DrefGlobalFilesSerializer,
    DrefOperationalUpdateSerializer,
    DrefSerializer,
    DrefShareUserSerializer,
    MiniDrefSerializer,
)
from dref.tasks import process_dref_translation
from main.permissions import DenyGuestUserPermission

logger = logging.getLogger(__name__)


def filter_dref_queryset_by_user_access(user, queryset: models.QuerySet) -> models.QuerySet[Dref]:
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
        dref_qs = (
            Dref.objects.select_related("country")
            .prefetch_related(
                Prefetch(
                    "drefoperationalupdate_set",
                    queryset=DrefOperationalUpdate.objects.select_related("country").order_by("-created_at"),
                    to_attr="prefetched_operational_updates",
                ),
                "dreffinalreport__country",
            )
            .annotate(
                has_ops_update=Exists(DrefOperationalUpdate.objects.filter(dref=OuterRef("pk"))),
                unpublished_op_update_count=Count(
                    "drefoperationalupdate",
                    filter=~Q(drefoperationalupdate__status=Dref.Status.APPROVED),
                ),
                has_final_report=Exists(DrefFinalReport.objects.filter(dref=OuterRef("pk"))),
                unpublished_final_report_count=Count(
                    "dreffinalreport",
                    filter=~Q(dreffinalreport__status=Dref.Status.APPROVED),
                ),
            )
        )
        qs = (
            super()
            .get_queryset()
            .select_related("country")
            .prefetch_related(
                Prefetch("dref", queryset=dref_qs),
            )
        )
        return filter_dref_queryset_by_user_access(user, qs)


class ActiveDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MiniDrefSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = ActiveDrefFilterSet

    queryset = (
        Dref.objects.select_related(
            "country",
        )
        .prefetch_related(
            Prefetch(
                "drefoperationalupdate_set",
                queryset=DrefOperationalUpdate.objects.select_related("country").order_by("-created_at"),
                to_attr="prefetched_operational_updates",
            ),
            "dreffinalreport__country",
        )
        .order_by("-created_at")
        .filter(is_active=True)
    )

    def get_queryset(self):
        return filter_dref_queryset_by_user_access(
            self.request.user,
            super().get_queryset(),
        ).annotate(
            has_ops_update=Exists(
                DrefOperationalUpdate.objects.filter(dref=OuterRef("pk")),
            ),
            unpublished_op_update_count=Count(
                "drefoperationalupdate",
                filter=~Q(drefoperationalupdate__status=Dref.Status.APPROVED),
            ),
            has_final_report=Exists(
                DrefFinalReport.objects.filter(dref=OuterRef("pk")),
            ),
            unpublished_final_report_count=Count(
                "dreffinalreport",
                filter=~Q(dreffinalreport__status=Dref.Status.APPROVED),
            ),
        )


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


class Dref3ViewSet(viewsets.GenericViewSet):
    """Read-only listing of all DREF stages (application / operational
    updates / final report) as flat rows, backed by a single UNION ALL
    queryset across the three stage models: standard filters, ordering and
    limit/offset pagination.
    """

    # Allow unauthenticated access; anonymous users only see approved rows
    permission_classes = [permissions.AllowAny]
    lookup_field = "appeal_code"
    # Keep DRF's default lookup_value_regex ([^/.]+): appeal codes contain no
    # dots, and widening it to [^/]+ makes the detail route swallow the
    # `.json` / `.csv` format suffix that format_suffix_patterns appends.
    filter_backends = []  # all filtering happens (pre-union) in build_union_queryset

    def get_queryset(self):
        # For schema generation only; list/retrieve build their own querysets
        return Dref.objects.none()

    def get_serializer_class(self):
        # For schema generation only
        return Dref3Serializer

    def _row_identities(self, rows):
        return [(row["stage"], row["id"], row["appeal_code"]) for row in rows]

    def _row_identities_iter(self, rows):
        """Lazy variant for the export, so no full row list is materialized."""
        for row in rows:
            yield (row["stage"], row["id"], row["appeal_code"])

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="order_by",
                description=(
                    "Use 'created_at' or '-created_at' to order row groups by the first DREF application "
                    "created_at per appeal_code; any other value defaults to appeal_code ordering. "
                    "Rows of one appeal_code always stay contiguous (stage-major, then created_at)."
                ),
                required=False,
                type=str,
            )
        ]
    )
    def list(self, request, version=None):
        # One access filter shared by the queryset and the hydrator, so the
        # per-model user-access narrowing is computed once per request.
        access = Dref3AccessFilter(request.user)
        try:
            queryset = build_union_queryset(request.user, request.query_params, access=access)
        except EmptyResult:
            queryset = empty_union_queryset()

        hydrator = Dref3PageHydrator(request.user, access=access)

        export_param = request.query_params.get("export")
        if export_param and export_param.lower() == "csv":
            # CSV export intentionally bypasses pagination (full filtered set),
            # so it is streamed in chunks rather than serialized all at once.
            return dref3_csv_streaming_response(
                self._row_identities_iter(queryset.iterator(chunk_size=DREF3_CSV_CHUNK_SIZE)),
                hydrator.hydrate,
            )

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(hydrator.hydrate(self._row_identities(page)))

    def retrieve(self, request, *args, **kwargs):
        code = kwargs.get(self.lookup_field)
        hydrator = Dref3PageHydrator(request.user)
        data = hydrator.hydrate_codes([code])
        if not data:
            logger.warning("No Dref, Operational Update, or Final Report found with code '%s'.", code)
        return response.Response(data)

    def get_renderer_context(self):
        context = super().get_renderer_context()
        context["header"] = Dref3Serializer.Meta.fields
        return context
