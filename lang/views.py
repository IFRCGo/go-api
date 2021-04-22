from django.db import transaction

from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action as djaction
from rest_framework import (
    viewsets,
    response,
)

from django.conf import settings
from .permissions import LangStringPermission
from .serializers import (
    StringSerializer,
    LanguageBulkActionSerializer,
    LanguageBulkActionsSerializer,
)
from .models import String


class LanguageViewSet(viewsets.ViewSet):
    # TODO: Cache retrive response to file
    authentication_classes = (TokenAuthentication,)
    permission_classes = (LangStringPermission,)
    lookup_url_kwarg = 'pk'

    def list(self, request, version=None):
        languages = [
            {'code': code, 'title': title}
            for code, title in settings.LANGUAGES
        ]
        return response.Response({
            'count': len(languages),
            'results': languages,
        })

    def retrieve(self, request, pk=None, version=None):
        if pk == 'all':
            obj = StringSerializer(String.objects.all(), many=True).data
        else:
            languages = settings.LANGUAGES
            code, title = next((lang for lang in languages if lang[0] == pk), (None, None))

            obj = {
                'code': code,
                'title': title,
                'strings': StringSerializer(String.objects.filter(language=code), many=True).data,
            }

        return response.Response(obj)

    @transaction.atomic
    @djaction(
        detail=True,
        url_path='bulk-action',
        methods=('post',),
    )
    def bulk_action(self, request, pk=None, *args, **kwargs):
        actions = LanguageBulkActionsSerializer(data=request.data)
        actions.is_valid(raise_exception=True)

        lang = pk
        lang_strings_qs = String.objects.filter(language=lang)
        new_strings = []
        changed_strings = {}
        deleted_string_keys = []
        existing_string_keys = set(lang_strings_qs.values_list('key', flat=True))
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
            to_update_strings = list(lang_strings_qs.filter(key__in=changed_strings.keys()).all())
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
