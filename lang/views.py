from django.db import transaction
from django.db.models import Q
import functools
import operator

from drf_spectacular.utils import extend_schema
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action as djaction
from rest_framework import (
    viewsets,
    response,
    views,
    permissions,
    status
)
from django.conf import settings
from .permissions import LangStringPermission
from .serializers import (
    StringSerializer,
    LanguageBulkActionSerializer,
    LanguageBulkActionsSerializer,
    LanguageListSerializer,
    LanguageRetriveSerializer,
    LanguageBulkActionResponseSerializer,
    TransLatteSerializer,
)
from .models import String


class LanguageViewSet(viewsets.ViewSet):
    # TODO: Cache retrive response to file
    authentication_classes = (TokenAuthentication,)
    permission_classes = (LangStringPermission,)
    lookup_url_kwarg = "pk"

    @extend_schema(
        request=None,
        responses=LanguageListSerializer
    )
    def list(self, request, version=None):
        languages = [{"code": code, "title": title} for code, title in settings.LANGUAGES]
        return response.Response(
            {
                "count": len(languages),
                "results": languages,
            }
        )

    @extend_schema(
        request=None,
        responses=LanguageRetriveSerializer
    )
    def retrieve(self, request, pk=None, version=None):
        page_name = self.request.query_params.getlist("page_name")
        page_name_list = []
        for xs in page_name:
            for x in xs.split(","):
                page_name_list.append(x)
        if pk == "all":
            obj = StringSerializer(String.objects.all(), many=True).data
            if page_name:
                for page in page_name_list:
                    obj = StringSerializer(String.objects.filter(page_name__icontains=page), many=True).data
        else:
            languages = settings.LANGUAGES
            code, title = next((lang for lang in languages if lang[0] == pk), (None, None))
            if page_name:
                pages = (Q(page_name__icontains=page) for page in page_name_list)
                query = functools.reduce(operator.or_, pages)
                queryset = String.objects.filter(query, language=code)
                obj = {
                    "code": code,
                    "title": title,
                    "strings": StringSerializer(queryset, many=True).data,
                }
            else:
                obj = {
                    "code": code,
                    "title": title,
                    "strings": StringSerializer(String.objects.filter(language=code), many=True).data,
                }

        return response.Response(obj)

    @transaction.atomic
    @extend_schema(
        request=LanguageBulkActionsSerializer,
        responses=LanguageBulkActionResponseSerializer
    )
    @djaction(
        detail=True,
        url_path="bulk-action",
        methods=("post",),
    )
    def bulk_action(self, request, pk=None, *args, **kwargs):
        actions = LanguageBulkActionsSerializer(data=request.data)
        actions.is_valid(raise_exception=True)

        lang = pk
        lang_strings_qs = String.objects.filter(language=lang)
        existing_string_keys = set(lang_strings_qs.values_list("key", flat=True))
        new_strings = []
        changed_strings = {}
        deleted_string_keys = []
        # Extract Actions
        for meta in actions.validated_data["actions"]:
            action = meta["action"]
            key = meta["key"]
            value = meta.get("value")
            value_hash = meta.get("hash")
            page_name = meta.get("page_name")
            value_meta = {
                "value": value,
                "hash": value_hash,
                "page_name": page_name,
            }
            if action == LanguageBulkActionSerializer.SET:
                if key in existing_string_keys:
                    changed_strings[key] = value_meta
                else:
                    new_strings.append(String(language=lang, key=key, **value_meta))
            elif action == LanguageBulkActionSerializer.DELETE and key in existing_string_keys:
                deleted_string_keys.append(key)

        # DB Bulk Operations
        if len(new_strings):
            new_strings = String.objects.bulk_create(new_strings)
        if len(changed_strings):
            to_update_strings = list(lang_strings_qs.filter(key__in=changed_strings.keys()).all())
            for string in to_update_strings:
                string.value = changed_strings[string.key]["value"]
                string.hash = changed_strings[string.key]["hash"]
                string.page_name = changed_strings[string.key]["page_name"]
            String.objects.bulk_update(to_update_strings, ["value", "hash", "page_name"])
            changed_strings = to_update_strings
        if len(deleted_string_keys):
            String.objects.filter(key__in=deleted_string_keys).delete()

        return response.Response(
            {
                "new_strings": StringSerializer(new_strings, many=True).data,
                "updated_strings": StringSerializer(changed_strings, many=True).data,
                "deleted_strings_keys": deleted_string_keys,
            }
        )


class TransLatteView(views.APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        actions = request.data['actions']
        lang = settings.LANGUAGES[0][0]
        for data in actions:
            action = data['action']
            key = data['key']
            page_name = data['page_name']
            value = data['value']

            if action == 'add':
                serializer = TransLatteSerializer(
                    data={
                        'page_name': page_name,
                        'key': key,
                        'value': value,
                        'language': lang,
                    }
                )
                if serializer.is_valid():
                    serializer.save()
                    return response.Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif action == 'delete':
                String.objects.filter(page_name=page_name, key=key).delete()
            elif action == 'update':
                try:
                    data_to_update = String.objects.get(page_name=page_name, key=key)
                except String.DoesNotExist:
                    return response.Response(
                        {'error': 'Data not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                serializer = TransLatteSerializer(
                    data_to_update,
                    data={'value': value},
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return response.Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return response.Response({'error': 'Invalid action type'}, status=status.HTTP_400_BAD_REQUEST)
