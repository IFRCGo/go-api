from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    status
)
from rest_framework.decorators import action
from dref.models import (
    Dref,
    DrefFile,
    NationalSocietyAction,
    PlannedIntervention,
    IdentifiedNeed
)
from dref.serializers import (
    DrefSerializer,
    NationalSocietyActionSerializer,
    PlannedInterventionSerializer,
    IdentifiedNeedSerializer,
    DrefFileSerializer
)
from dref.filter_set import DrefFilter


class DrefViewSet(viewsets.ModelViewSet):
    # TODO: Need to add permission to delete?
    serializer_class = DrefSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DrefFilter

    def get_queryset(self):
        return Dref.objects.prefetch_related(
            'planned_interventions', 'needs_identified', 'national_society_actions'
        )


class DrefOptionsView(views.APIView):
    """
    Options for various attrivute related to Dref
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
            ]
        }
        return response.Response(options)


class NationalSocietyActionViewSet(viewsets.ModelViewSet):
    serializer_class = NationalSocietyActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = NationalSocietyAction.objects.all()


class PlannedInterventionViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedInterventionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PlannedIntervention.objects.all()


class IdentifiedNeedViewSet(viewsets.ModelViewSet):
    serializer_class = IdentifiedNeedSerializer
    permission_class = [permissions.IsAuthenticated]
    queryset = IdentifiedNeed.objects.all()


class DrefFileViewSet(viewsets.ModelViewSet):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = DrefFileSerializer
    queryset = DrefFile.objects.all()

    @action(
        detail=False,
        url_path='multiple',
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        def modify_input_for_multiple_files(file):
            dict = {}
            dict['file'] = file
            return dict
        # converts querydict to original dict
        files = dict((request.data).lists())['file']
        flag = 1
        arr = []
        for file in files:
            modified_data = modify_input_for_multiple_files(file)
            file_serializer = DrefFileSerializer(data=modified_data)
            if file_serializer.is_valid():
                file_serializer.save()
                arr.append(file_serializer.data)
            else:
                flag = 0

        if flag == 1:
            return response.Response(arr, status=status.HTTP_201_CREATED)
        else:
            return response.Response(arr, status=status.HTTP_400_BAD_REQUEST)
