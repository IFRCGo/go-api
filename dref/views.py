from itertools import chain
from operator import attrgetter

from django.utils.translation import gettext
import django.utils.timezone as timezone
from reversion.views import RevisionMixin
from django.contrib.auth.models import Permission
from django.db import models

from drf_spectacular.utils import extend_schema_view
from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    status,
    mixins,
    serializers,
)
from rest_framework.decorators import action
from dref.models import (
    Dref,
    NationalSocietyAction,
    PlannedIntervention,
    IdentifiedNeed,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
)
from dref.serializers import (
    DrefSerializer,
    DrefFileSerializer,
    DrefOperationalUpdateSerializer,
    DrefFinalReportSerializer,
    CompletedDrefOperationsSerializer,
    MiniDrefSerializer,
    AddDrefUserSerializer,
    DrefShareUserSerializer,
    DrefOptionsSerializer,
    IntegerKeyValueSerializer
)
from deployments.serializers import CharKeyValueSerializer
from dref.filter_set import (
    DrefFilter,
    DrefOperationalUpdateFilter,
    CompletedDrefOperationsFilterSet,
    ActiveDrefFilterSet,
    DrefShareUserFilterSet,
)
from dref.permissions import PublishDrefPermission


def filter_dref_queryset_by_user_access(user, queryset):
    if user.is_superuser:
        return queryset
    # Check if regional admin
    dref_admin_regions_id = [
        codename.replace('dref_region_admin_', '')
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith='dref_region_admin_',
        ).values_list('codename', flat=True)
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


class DrefOptionsView(views.APIView):
    """
    Options for various attribute related to Dref
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses=DrefOptionsSerializer)
    def get(self, request, version=None):
        return response.Response(DrefOptionsSerializer(
            dict(
                status=IntegerKeyValueSerializer.choices_to_data(Dref.Status.choices),
                type_of_onset=IntegerKeyValueSerializer.choices_to_data(Dref.OnsetType.choices),
                disaster_category=IntegerKeyValueSerializer.choices_to_data(Dref.DisasterCategory.choices),
                planned_interventions=CharKeyValueSerializer.choices_to_data(PlannedIntervention.Title.choices),
                needs_identified=CharKeyValueSerializer.choices_to_data(IdentifiedNeed.Title.choices),
                national_society_actions=CharKeyValueSerializer.choices_to_data(NationalSocietyAction.Title.choices),
                type_of_dref=IntegerKeyValueSerializer.choices_to_data(Dref.DrefType.choices),
            )
        ).data
    )



class DrefFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = DrefFileSerializer

    def get_queryset(self):
        if self.request is None:
            return DrefFile.objects.none()
        return DrefFile.objects.filter(created_by=self.request.user)

    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = [
            files[0]
            for files in dict((request.data).lists()).values()
        ]
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

    def get_queryset(self):
        user = self.request.user
        queryset = DrefFinalReport.objects.filter(is_published=True).order_by("-created_at").distinct()
        return filter_dref_queryset_by_user_access(user, queryset)


@extend_schema_view(request=None, responses=MiniDrefSerializer)
class ActiveDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MiniDrefSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ActiveDrefFilterSet

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            dref = (
                Dref.objects.prefetch_related(
                    "planned_interventions", "needs_identified", "national_society_actions", "users"
                ).distinct()
            )
            dref_op_update = (
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
                ).order_by('-operational_update_number').distinct()
            )
            dref_final_report = (
                DrefFinalReport.objects.prefetch_related(
                    "dref__planned_interventions",
                    "dref__needs_identified",
                ).distinct()
            )
            result_list = sorted(chain(dref, dref_op_update, dref_final_report), key=attrgetter("created_at"), reverse=True)
            dref_list = []
            for data in result_list:
                if data.__class__.__name__ == "DrefFinalReport":
                    final_report = DrefFinalReport.objects.get(id=data.id)
                    dref_list.append(final_report)
                elif data.__class__.__name__ == "DrefOperationalUpdate":
                    operational_update = DrefOperationalUpdate.objects.get(id=data.id)
                    dref_list.append(operational_update)
                elif data.__class__.__name__ == "Dref":
                    dref = Dref.objects.get(id=data.id)
                    dref_list.append(dref)
            # iterate over the list and get the dref from that
            # check the dref in the new list if exists
            # annotated dref here
            annoatated_drefs = []
            for dref in dref_list:
                if dref.__class__.__name__ == "DrefOperationalUpdate":
                    # annotate the dref and other operational update for that dref
                    operational_update = DrefOperationalUpdate.objects.get(id=dref.id)
                    dref_object = Dref.objects.get(drefoperationalupdate=operational_update.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
                elif dref.__class__.__name__ == "Dref":
                    dref_object = Dref.objects.get(id=dref.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
                elif dref.__class__.__name__ == "DrefFinalReport":
                    final_report = DrefFinalReport.objects.get(id=dref.id)
                    dref_object = Dref.objects.get(dreffinalreport=final_report.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
            dref_list = []
            for dref in annoatated_drefs:
                new_dref = Dref.objects.get(id=dref.id)
                dref_list.append(new_dref.id)
            return Dref.objects.filter((models.Q(id__in=dref_list) | models.Q(created_by=user) | models.Q(users=user)), is_active=True).distinct().order_by("-created_at")
        elif not user.is_superuser:
            # get current user dref regions
            regions = [0, 1, 2, 3, 4]
            final_report_list = []
            for region in regions:
                codename = f"dref_region_admin_{region}"
                if Permission.objects.filter(group__user=user, codename=codename).exists():
                    dref = (
                        Dref.objects.prefetch_related(
                            "planned_interventions", "needs_identified", "national_society_actions", "users"
                        )
                        .filter(country__region=region)
                        .distinct()
                    )
                    dref_op_update = (
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
                        .filter(country__region=region)
                        .order_by('-operational_update_number').distinct()
                    )
                    dref_final_report = (
                        DrefFinalReport.objects.prefetch_related(
                            "dref__planned_interventions",
                            "dref__needs_identified",
                        )
                        .filter(country__region=region)
                        .distinct()
                    )
                    result_list = sorted(chain(dref, dref_op_update, dref_final_report), key=attrgetter("created_at"), reverse=True)
                    final_report_list.append(result_list)
            dref_list = []
            for data in final_report_list:
                for new in data:
                    if new.__class__.__name__ == "DrefFinalReport":
                        final_report = DrefFinalReport.objects.get(id=new.id)
                        dref_list.append(final_report)
                    elif new.__class__.__name__ == "DrefOperationalUpdate":
                        operational_update = DrefOperationalUpdate.objects.get(id=new.id)
                        dref_list.append(operational_update)
                    elif new.__class__.__name__ == "Dref":
                        dref = Dref.objects.get(id=new.id)
                        dref_list.append(dref)
            # iterate over the list and get the dref from that
            # check the dref in the new list if exists
            # annotated dref here
            annoatated_drefs = []
            for dref in dref_list:
                if dref.__class__.__name__ == "DrefOperationalUpdate":
                    # annotate the dref and other operational update for that dref
                    operational_update = DrefOperationalUpdate.objects.get(id=dref.id)
                    dref_object = Dref.objects.get(drefoperationalupdate=operational_update.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
                elif dref.__class__.__name__ == "Dref":
                    dref_object = Dref.objects.get(id=dref.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
                elif dref.__class__.__name__ == "DrefFinalReport":
                    final_report = DrefFinalReport.objects.get(id=dref.id)
                    dref_object = Dref.objects.get(dreffinalreport=final_report.id)
                    if dref_object not in annoatated_drefs:
                        annoatated_drefs.append(dref_object)
            dref_list = []
            for dref in annoatated_drefs:
                new_dref = Dref.objects.get(id=dref.id)
                dref_list.append(new_dref.id)
            if len(dref_list):
                return Dref.objects.filter((models.Q(id__in=dref_list) | models.Q(created_by=user) | models.Q(users=user)), is_active=True).distinct().order_by("-created_at")
            else:
                dref = Dref.get_for(user)
                dref_op_update = DrefOperationalUpdate.get_for(user)
                dref_final_report = DrefFinalReport.get_for(user)
                result_list = sorted(chain(dref, dref_op_update, dref_final_report), key=attrgetter("created_at"), reverse=True)
                dref_list = []
                for data in result_list:
                    if data.__class__.__name__ == "DrefFinalReport":
                        final_report = DrefFinalReport.objects.get(id=data.id)
                        dref_list.append(final_report)
                    elif data.__class__.__name__ == "DrefOperationalUpdate":
                        operational_update = DrefOperationalUpdate.objects.get(id=data.id)
                        dref_list.append(operational_update)
                    elif data.__class__.__name__ == "Dref":
                        dref = Dref.objects.get(id=data.id)
                        dref_list.append(dref)
                # iterate over the list and get the dref from that
                # check the dref in the new list if exists
                # annotated dref here
                annoatated_drefs = []
                for dref in dref_list:
                    if dref.__class__.__name__ == "DrefOperationalUpdate":
                        # annotate the dref and other operational update for that dref
                        operational_update = DrefOperationalUpdate.objects.get(id=dref.id)
                        dref_object = Dref.objects.get(drefoperationalupdate=operational_update.id)
                        if dref_object not in annoatated_drefs:
                            annoatated_drefs.append(dref_object)
                    elif dref.__class__.__name__ == "Dref":
                        dref_object = Dref.objects.get(id=dref.id)
                        if dref_object not in annoatated_drefs:
                            annoatated_drefs.append(dref_object)
                    elif dref.__class__.__name__ == "DrefFinalReport":
                        final_report = DrefFinalReport.objects.get(id=dref.id)
                        dref_object = Dref.objects.get(dreffinalreport=final_report.id)
                        if dref_object not in annoatated_drefs:
                            annoatated_drefs.append(dref_object)
                dref_list = []
                for dref in annoatated_drefs:
                    new_dref = Dref.objects.get(id=dref.id)
                    dref_list.append(new_dref.id)
                return Dref.objects.filter(id__in=dref_list, is_active=True).order_by("-created_at")


class DrefShareView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

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
