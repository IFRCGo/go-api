from itertools import chain
from operator import attrgetter

from django.contrib.auth.models import User
from django.utils.translation import gettext
from reversion.views import RevisionMixin

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
    MiniOperationalUpdateSerializer,
    MiniDrefSerializer,
    AddDrefUserSerializer
)
from dref.filter_set import (
    DrefFilter,
    DrefOperationalUpdateFilter,
    CompletedDrefOperationsFilterSet,
)
from dref.permissions import (
    DrefOperationalUpdateUpdatePermission,
    DrefFinalReportUpdatePermission,
    PublishDrefPermission
)


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
        dref.save(update_fields=["is_published"])
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
        operational_update.save(update_fields=["is_published"])
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
        field_report.save(update_fields=["is_published"])
        if not field_report.dref.is_final_report_created:
            field_report.dref.is_final_report_created = True
            field_report.dref.save(update_fields=["is_final_report_created"])
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
            "type_of_dref": [{"key": dref_type.value, "value": dref_type.label} for dref_type in Dref.DrefType]
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
        queryset = (
            DrefFinalReport.objects.filter(is_published=True)
            .order_by("-created_at")
            .distinct()
        )
        if user.is_superuser:
            return queryset
        else:
            return DrefFinalReport.get_for(user)


class ActiveDrefOperationsViewSet(views.APIView):
    # serializer_class = CompletedDrefOperationsSerializer
    permission_classes = [permissions.IsAuthenticated]
    # filterset_class = CompletedDrefOperationsFilterSet

    def get(self, request, version=None):
        user = self.request.user
        dref = Dref.get_for(user)
        dref_op_update = DrefOperationalUpdate.get_for(user)
        dref_final_report = DrefFinalReport.get_for(user)
        result_list = sorted(
            chain(dref, dref_op_update, dref_final_report),
            key=attrgetter('created_at'),
            reverse=True
        )
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
        serializer = MiniOperationalUpdateSerializer(dref_list, many=True)
        return response.Response({"status": "success", "data": serializer.data})


class DrefShareView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddDrefUserSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(status=status.HTTP_200_OK)
