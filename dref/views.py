from django.db import models
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
)
from dref.filter_set import (
    DrefFilter,
    DrefOperationalUpdateFilter
)
from dref.permissions import (
    DrefViewUpdatePermission,
    DrefOperationalUpdateCreatePermission,
)


class DrefViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefSerializer
    permission_classes = [permissions.IsAuthenticated, DrefViewUpdatePermission]
    filterset_class = DrefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Dref.objects.prefetch_related(
            'planned_interventions',
            'needs_identified',
            'national_society_actions',
            'users'
        ).order_by('-created_at').distinct()
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(models.Q(created_by=user) | models.Q(users=user))

    @action(
        detail=True,
        url_path='publish',
        methods=['post'],
        serializer_class=DrefSerializer,
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_published(self, request, pk=None, version=None):
        dref = self.get_object()
        if not dref.is_published:
            dref.is_published = True
            dref.save(update_fields=['is_published'])
        serializer = DrefSerializer(dref, context={'request': request})
        return response.Response(serializer.data)


class DrefOperationalUpdateViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefOperationalUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DrefOperationalUpdateFilter

    def get_queryset(self):
        user = self.request.user
        queryset = DrefOperationalUpdate.objects.select_related(
            'national_society',
            'national_society',
            'disaster_type',
            'event_map',
            'cover_image',
            'budget_file',
            'assessment_report'
        ).prefetch_related(
            'dref',
            'planned_interventions',
            'needs_identified',
            'national_society_actions',
            'users',
            'images',
            'photos',
        ).order_by('-created_at').distinct()
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(models.Q(created_by=user) | models.Q(users=user))

    @action(
        detail=True,
        url_path='publish',
        methods=['post'],
        serializer_class=DrefOperationalUpdateSerializer,
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_published(self, request, pk=None, version=None):
        operational_update = self.get_object()
        if not operational_update.is_published:
            operational_update.is_published = True
            operational_update.save(update_fields=['is_published'])
        serializer = DrefOperationalUpdateSerializer(operational_update, context={'request': request})
        return response.Response(serializer.data)


class DrefFinalReportViewSet(RevisionMixin, viewsets.ModelViewSet):
    serializer_class = DrefFinalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DrefFinalReport.objects.prefetch_related(
            'dref__planned_interventions',
            'dref__needs_identified',
        ).order_by('-created_at').distinct()

    @action(
        detail=True,
        url_path='publish',
        methods=['post'],
        serializer_class=DrefFinalReportSerializer,
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_published(self, request, pk=None, version=None):
        field_report = self.get_object()
        if field_report.is_published:
            raise serializers.ValidationError(
                gettext('Final Report %s is already published' % field_report)
            )
        if not field_report.is_published:
            field_report.is_published = True
            field_report.save(update_fields=['is_published'])
        if not field_report.dref.is_final_report_created:
            field_report.dref.is_final_report_created = True
            field_report.dref.save(update_fields=['is_final_report_created'])
        serializer = DrefFinalReportSerializer(field_report, context={'request': request})
        return response.Response(serializer.data)


class DrefOptionsView(views.APIView):
    """
    Options for various attribute related to Dref
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = {
            'status': [
                {
                    'key': status.value,
                    'value': status.label
                } for status in Dref.Status
            ],
            'type_of_onset': [
                {
                    'key': onset.value,
                    'value': onset.label
                } for onset in Dref.OnsetType
            ],
            'disaster_category': [
                {
                    'key': disaster.value,
                    'value': disaster.label
                } for disaster in Dref.DisasterCategory
            ],
            'planned_interventions': [
                {
                    'key': intervention[0],
                    'value': intervention[1]
                } for intervention in PlannedIntervention.Title.choices
            ],
            'needs_identified': [
                {
                    'key': need[0],
                    'value': need[1]
                } for need in IdentifiedNeed.Title.choices
            ],
            'national_society_actions': [
                {
                    'key': action[0],
                    'value': action[1]
                } for action in NationalSocietyAction.Title.choices
            ],
            'users': [
                {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                } for user in User.objects.filter(is_active=True)
            ]
        }
        return response.Response(options)


class DrefFileViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = DrefFileSerializer

    def get_queryset(self):
        if self.request is None:
            return DrefFile.objects.none()
        return DrefFile.objects.filter(created_by=self.request.user)

    @action(
        detail=False,
        url_path='multiple',
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = dict((request.data).lists())['file']
        data = [{'file': file} for file in files]
        file_serializer = DrefFileSerializer(data=data, context={'request': request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
