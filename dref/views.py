from itertools import chain
from operator import attrgetter

from django.utils.translation import gettext
import django.utils.timezone as timezone
from reversion.views import RevisionMixin
from django.contrib.auth.models import Permission

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
)
from dref.filter_set import (
    DrefFilter,
    DrefOperationalUpdateFilter,
    CompletedDrefOperationsFilterSet,
    ActiveDrefFilterSet,
    DrefShareUserFilterSet,
)
from dref.permissions import PublishDrefPermission


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
        if user.is_superuser:
            return queryset
        else:
            return Dref.get_for(user)

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
        if user.is_superuser:
            return queryset
        else:
            return DrefOperationalUpdate.get_for(user)

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
        if user.is_superuser:
            return queryset
        else:
            return DrefFinalReport.get_for(user)

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
        if not field_report.dref.is_final_report_created:
            field_report.dref.is_final_report_created = True
            field_report.date_of_approval = timezone.now().date()
            field_report.dref.save(update_fields=["is_final_report_created", "date_of_approval"])
        serializer = DrefFinalReportSerializer(field_report, context={"request": request})
        return response.Response(serializer.data)


class DrefOptionsView(views.APIView):
    """
    Options for various attribute related to Dref
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = {
            "status": [{"key": status.value, "value": status.label} for status in Dref.Status],
            "type_of_onset": [{"key": onset.value, "value": onset.label} for onset in Dref.OnsetType],
            "disaster_category": [{"key": disaster.value, "value": disaster.label} for disaster in Dref.DisasterCategory],
            "planned_interventions": [
                {"key": intervention[0], "value": intervention[1]} for intervention in PlannedIntervention.Title.choices
            ],
            "needs_identified": [{"key": need[0], "value": need[1]} for need in IdentifiedNeed.Title.choices],
            "national_society_actions": [
                {"key": action[0], "value": action[1]} for action in NationalSocietyAction.Title.choices
            ],
            "type_of_dref": [{"key": dref_type.value, "value": dref_type.label} for dref_type in Dref.DrefType],
        }
        return response.Response(options)


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
        files = dict((request.data).lists())["file"]
        data = [{"file": file} for file in files]
        file_serializer = DrefFileSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompletedDrefOperationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompletedDrefOperationsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = CompletedDrefOperationsFilterSet

    def get_queryset(self):
        user = self.request.user
        queryset = DrefFinalReport.objects.filter(is_published=True).order_by("-created_at").distinct()
        if user.is_superuser:
            return queryset
        else:
            regions = [0, 1, 2, 3, 4]
            for region in regions:
                codename = f"dref_region_admin_{region}"
                if Permission.objects.filter(user=user, codename=codename).exists():
                    final_report = (
                        DrefFinalReport.objects.prefetch_related(
                            "dref__planned_interventions",
                            "dref__needs_identified",
                        )
                        .filter(country__region=region, is_published=True)
                        .distinct()
                    )
                    return final_report
                else:
                    return DrefFinalReport.get_for(user, is_published=True)


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
                )
                .filter(is_final_report_created=False)
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
                .filter(dref__is_final_report_created=False)
                .distinct()
            )
            dref_final_report = (
                DrefFinalReport.objects.prefetch_related(
                    "dref__planned_interventions",
                    "dref__needs_identified",
                )
                .filter(dref__is_final_report_created=False)
                .distinct()
            )
        else:
            # get current user dref regions
            regions = [0, 1, 2, 3, 4]
            for region in regions:
                codename = f"dref_region_admin_{region}"
                if Permission.objects.filter(user=user, codename=codename).exists():
                    dref = (
                        Dref.objects.prefetch_related(
                            "planned_interventions", "needs_identified", "national_society_actions", "users"
                        )
                        .filter(country__region=region, is_final_report_created=False)
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
                        .filter(country__region=region, dref__is_final_report_created=False)
                        .distinct()
                    )
                    dref_final_report = (
                        DrefFinalReport.objects.prefetch_related(
                            "dref__planned_interventions",
                            "dref__needs_identified",
                        )
                        .filter(country__region=region, dref__is_final_report_created=False)
                        .distinct()
                    )
                else:
                    dref = Dref.get_for(user).filter(dref__is_final_report_created=False)
                    dref_op_update = DrefOperationalUpdate.get_for(user).filter(dref__is_final_report_created=False)
                    dref_final_report = DrefFinalReport.get_for(user).filter(dref__is_final_report_created=False)
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
        return Dref.objects.filter(id__in=dref_list).order_by("-created_at")


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
