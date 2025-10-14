import django.utils.timezone as timezone
from django.contrib.auth.models import Permission
from django.db import models
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

from dref.filter_set import (
    ActiveDrefFilterSet,
    CompletedDrefOperationsFilterSet,
    DrefFilter,
    DrefOperationalUpdateFilter,
    DrefShareUserFilterSet,
)
from dref.models import Dref, DrefFile, DrefFinalReport, DrefOperationalUpdate
from dref.permissions import PublishDrefPermission
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
from dref.utils import is_translation_complete
from main.permissions import DenyGuestUserPermission, UseBySuperAdminOnly


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

    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        serializer_class=DrefSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        dref = self.get_object()
        if dref.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved"))
        if dref.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("Dref %s is already approved" % dref))
        dref.status = Dref.Status.APPROVED
        dref.save(update_fields=["status"])
        serializer = DrefSerializer(dref, context={"request": request})
        return response.Response(serializer.data)

    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        serializer_class=DrefSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        dref = self.get_object()
        if dref.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(gettext("Cannot be finalized because it is already %s") % dref.get_status_display())

        if not is_translation_complete(dref):
            raise serializers.ValidationError("Cannot be finalized because translation is not completed")
        fields_to_update = ["status"]
        if dref.translation_module_original_language != "en":
            dref.translation_module_original_language = "en"
            fields_to_update.append("translation_module_original_language")
        dref.status = Dref.Status.FINALIZED
        dref.save(update_fields=fields_to_update)
        serializer = DrefSerializer(dref, context={"request": request})
        return response.Response(serializer.data)

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

    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        serializer_class=DrefOperationalUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        operational_update = self.get_object()
        if operational_update.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved."))
        if operational_update.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("Operational update %s is already approved" % operational_update))
        operational_update.status = Dref.Status.APPROVED
        operational_update.save(update_fields=["status"])
        serializer = DrefOperationalUpdateSerializer(operational_update, context={"request": request})
        return response.Response(serializer.data)

    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        serializer_class=DrefOperationalUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        operational_update = self.get_object()
        if operational_update.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(
                gettext("Cannot be finalized because it is already %s") % operational_update.get_status_display()
            )
        if not is_translation_complete(operational_update):
            raise serializers.ValidationError("Cannot be finalized because translation is not completed")
        fields_to_update = ["status"]
        if operational_update.translation_module_original_language != "en":
            operational_update.translation_module_original_language = "en"
            fields_to_update.append("translation_module_original_language")
        operational_update.status = Dref.Status.FINALIZED
        operational_update.save(update_fields=fields_to_update)
        serializer = DrefOperationalUpdateSerializer(operational_update, context={"request": request})
        return response.Response(serializer.data)


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

    @action(
        detail=True,
        url_path="approve",
        methods=["post"],
        serializer_class=DrefFinalReportSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission, DenyGuestUserPermission],
    )
    def get_approved(self, request, pk=None, version=None):
        field_report = self.get_object()
        if field_report.status != Dref.Status.FINALIZED:
            raise serializers.ValidationError(gettext("Must be finalized before it can be approved."))
        if field_report.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("Final Report %s is already approved" % field_report))
        field_report.status = Dref.Status.APPROVED
        field_report.save(update_fields=["status"])
        field_report.dref.is_active = False
        field_report.date_of_approval = timezone.now().date()
        field_report.dref.save(update_fields=["is_active", "date_of_approval"])
        serializer = DrefFinalReportSerializer(field_report, context={"request": request})
        return response.Response(serializer.data)

    @action(
        detail=True,
        url_path="finalize",
        methods=["post"],
        serializer_class=DrefFinalReportSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def finalize(self, request, pk=None, version=None):
        field_report = self.get_object()
        if field_report.status in [Dref.Status.FINALIZED, Dref.Status.APPROVED]:
            raise serializers.ValidationError(
                gettext("Cannot be finalized because it is already %s") % field_report.get_status_display()
            )
        if not is_translation_complete(field_report):
            raise serializers.ValidationError("Cannot be finalized because translation is not completed")
        fields_to_update = ["status"]
        if field_report.translation_module_original_language != "en":
            field_report.translation_module_original_language = "en"
            fields_to_update.append("translation_module_original_language")
        field_report.status = Dref.Status.FINALIZED
        field_report.save(update_fields=fields_to_update)
        serializer = DrefFinalReportSerializer(field_report, context={"request": request})
        return response.Response(serializer.data)


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


class Dref3ViewSet(RevisionMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission, UseBySuperAdminOnly]
    #    serializer_class = DrefSerializer
    #    filterset_class = DrefFilter
    lookup_field = "appeal_code"

    def get_queryset(self):
        # just to give something to rest_framework/generics.py:63 – not used in retrieve
        return Dref.objects.none()

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

        codes_qs = Dref.objects.exclude(appeal_code="").values_list("appeal_code", flat=True).distinct().order_by("appeal_code")

        # Filtering by appeal_code prefix
        appeal_code_prefix = request.query_params.get("appeal_code_prefix")
        if appeal_code_prefix:
            codes_qs = codes_qs.filter(appeal_code__startswith=appeal_code_prefix)

        # Filtering by different date ranges
        for field in [
            "event_date",
            "ns_respond_date",
            "government_requested_assistance_date",
            "ns_request_date",
            "submission_to_geneva",
            "date_of_approval",
            "publishing_date",
            "hazard_date_and_location",
            "end_date",
        ]:
            from_param = f"{field}_from"
            to_param = f"{field}_to"
            from_value = request.query_params.get(from_param)
            to_value = request.query_params.get(to_param)
            if from_value:
                codes_qs = codes_qs.filter(**{f"{field}__gte": from_value})
            if to_value:
                codes_qs = codes_qs.filter(**{f"{field}__lte": to_value})

        codes = list(codes_qs)

        data = []
        old_kwargs = getattr(self, "kwargs", {}).copy()
        for code in codes:
            self.kwargs = {self.lookup_field: code}
            resp = self.retrieve(request)
            if resp.status_code == 200:
                for item in resp.data if isinstance(resp.data, list) else [resp.data]:
                    data.append(item)
        self.kwargs = old_kwargs  # Restore old kwargs
        return response.Response(data)

    def get_serializer_class(self):
        # just to give something to rest_framework/generics.py:122 – not used in retrieve
        return Dref3Serializer

    #    def get_renderers(self):
    #        return [renderer() for renderer in tuple(api_settings.DEFAULT_RENDERER_CLASSES)]

    def get_objects_by_appeal_code(self, appeal_code):
        results = []
        user = self.request.user
        drefs = (
            Dref.objects.filter(appeal_code=appeal_code)
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("created_at")
            .distinct()
        )
        drefs = filter_dref_queryset_by_user_access(user, drefs)
        if drefs.exists():
            results.extend(drefs)

        # Code duplication of the previous "drefs" for "operational_updates" and "final_reports" until ¤¤¤:
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
        # ¤¤¤

        return results

    def retrieve(self, request, *args, **kwargs):
        code = self.kwargs.get(self.lookup_field)
        instances = self.get_objects_by_appeal_code(code)

        if not instances:
            raise NotFound(f"No Dref, Operational Update, or Final Report found with code '{code}'.")

        serialized_data = []
        ops_update_count = 0
        allocation_count = 1  # Dref Application is always the first allocation
        a = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
        for instance in instances:
            if isinstance(instance, Dref):
                serializer = Dref3Serializer(instance, context={"stage": "Application", "allocation": a[0]})
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
                        "stage": "Operational Update " + str(ops_update_count),
                        "allocation": allocation,
                    },
                )
            elif isinstance(instance, DrefFinalReport):
                serializer = DrefFinalReport3Serializer(
                    instance, context={"stage": "Final Report", "allocation": "No allocation"}
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
