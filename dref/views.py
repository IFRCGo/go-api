from itertools import chain
from operator import attrgetter

import django.utils.timezone as timezone
from django.contrib.auth.models import Permission
from django.db import models
from django.utils.translation import gettext
from drf_spectacular.utils import extend_schema, extend_schema_view
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
    DrefFileInputSerializer,
    DrefFileSerializer,
    DrefFinalReportSerializer,
    DrefOperationalUpdateSerializer,
    DrefSerializer,
    DrefShareUserSerializer,
    MiniDrefSerializer,
)


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
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DrefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Dref.objects.prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("-created_at")
            .distinct()
        )
        return filter_dref_queryset_by_user_access(user, queryset)

    @action(
        detail=True,
        url_path="publish",
        methods=["post"],
        serializer_class=DrefSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission],
    )
    def get_published(self, request, pk=None, version=None):
        dref = self.get_object()
        dref.is_published = True
        dref.status = Dref.Status.COMPLETED
        dref.save(update_fields=["is_published", "status"])
        serializer = DrefSerializer(dref, context={"request": request})
        return response.Response(serializer.data)


class DrefOperationalUpdateViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefOperationalUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
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
        url_path="publish",
        methods=["post"],
        serializer_class=DrefOperationalUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission],
    )
    def get_published(self, request, pk=None, version=None):
        operational_update = self.get_object()
        operational_update.is_published = True
        operational_update.status = Dref.Status.COMPLETED
        operational_update.save(update_fields=["is_published", "status"])
        serializer = DrefOperationalUpdateSerializer(operational_update, context={"request": request})
        return response.Response(serializer.data)


class DrefFinalReportViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefFinalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        url_path="publish",
        methods=["post"],
        serializer_class=DrefFinalReportSerializer,
        permission_classes=[permissions.IsAuthenticated, PublishDrefPermission],
    )
    def get_published(self, request, pk=None, version=None):
        field_report = self.get_object()
        if field_report.is_published:
            raise serializers.ValidationError(gettext("Final Report %s is already published" % field_report))
        field_report.is_published = True
        field_report.status = Dref.Status.COMPLETED
        field_report.save(update_fields=["is_published", "status"])
        field_report.dref.is_active = False
        field_report.date_of_approval = timezone.now().date()
        field_report.dref.save(update_fields=["is_active", "date_of_approval"])
        serializer = DrefFinalReportSerializer(field_report, context={"request": request})
        return response.Response(serializer.data)


class DrefFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_class = [permissions.IsAuthenticated]
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
        permission_classes=[permissions.IsAuthenticated],
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
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = CompletedDrefOperationsFilterSet
    queryset = DrefFinalReport.objects.filter(is_published=True).order_by("-created_at").distinct()

    def get_queryset(self):
        user = self.request.user
        return filter_dref_queryset_by_user_access(user, super().get_queryset())


class ActiveDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MiniDrefSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=AddDrefUserSerializer, responses=None)
    def post(self, request):
        serializer = AddDrefUserSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(status=status.HTTP_200_OK)


class DrefShareUserViewSet(viewsets.ReadOnlyModelViewSet):
    permissions_classes = [permissions.IsAuthenticated]
    serializer_class = DrefShareUserSerializer
    filterset_class = DrefShareUserFilterSet

    def get_queryset(self):
        return (
            Dref.objects.prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users")
            .order_by("-created_at")
            .distinct()
        )
