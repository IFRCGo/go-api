from django.db import transaction
from rest_framework.decorators import action as djaction
from rest_framework import (
    viewsets,
    response,
)

from main.permissions import ModifyBySuperAdminOnly
from .serializers import (
    LanguageSerializer,
    ListLanguageSerializer,
    StringSerializer,
    LanguageBulkActionSerializer,
    LanguageBulkActionsSerializer,
)
from .models import (
    Language,
    String,
)


class LanguageViewSet(viewsets.ModelViewSet):
    # TODO: Add permission level
    # TODO: Cache retrive response to file
    permission_classes = (ModifyBySuperAdminOnly,)
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    lookup_url_kwarg = 'pk'

    def get_object(self):
        """
        Retrive object by using id or code.
        """
        pk = self.kwargs[self.lookup_url_kwarg]
        try:
            pk = int(pk)
        except ValueError:  # If it's string
            self.lookup_field = 'code'
        return super().get_object()

    def get_serializer_class(self):
        if self.action == 'list':
            return ListLanguageSerializer
        return super().get_serializer_class()

    @transaction.atomic
    @djaction(
        detail=True, url_path='bulk-action',
        methods=('post',),
        serializer_class=LanguageBulkActionsSerializer,
    )
    def bulk_action(self, request, *args, **kwargs):
        lang = self.get_object()
        actions = self.serializer_class(data=request.data)
        actions.is_valid(raise_exception=True)

        new_strings = []
        changed_strings = {}
        deleted_string_keys = []
        existing_string_keys = set(lang.string_set.values_list('key', flat=True))
        # Extract Actions
        for meta in actions.validated_data['actions']:
            action = meta['action']
            key = meta['key']
            value = meta.get('value')
            value_hash = meta.get('hash')
            value_meta = {
                'value': value,
                'hash': value_hash,
            }
            if action == LanguageBulkActionSerializer.SET:
                if key in existing_string_keys:
                    changed_strings[key] = value_meta
                else:
                    new_strings.append(
                        String(language=lang, key=key, **value_meta)
                    )
            elif action == LanguageBulkActionSerializer.DELETE and key in existing_string_keys:
                deleted_string_keys.append(key)

        # DB Bulk Operations
        if len(new_strings):
            new_strings = String.objects.bulk_create(new_strings)
        if len(changed_strings):
            to_update_strings = list(lang.string_set.filter(key__in=changed_strings.keys()).all())
            for string in to_update_strings:
                string.value = changed_strings[string.key]['value']
                string.hash = changed_strings[string.key]['hash']
            String.objects.bulk_update(to_update_strings, ['value', 'hash'])
            changed_strings = to_update_strings
        if len(deleted_string_keys):
            String.objects.filter(key__in=deleted_string_keys).delete()

        return response.Response({
            'new_strings': StringSerializer(new_strings, many=True).data,
            'updated_strings': StringSerializer(changed_strings, many=True).data,
            'deleted_strings_keys': deleted_string_keys,
        })
