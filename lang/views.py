import functools
import operator
import typing

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import response, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action as djaction

from .models import String
from .permissions import LangStringPermission
from .serializers import (
    LanguageBulkActionResponseSerializer,
    LanguageBulkActionSerializer,
    LanguageBulkActionsSerializer,
    LanguageListSerializer,
    LanguageRetriveSerializer,
    StringSerializer,
)


class LanguageViewSet(viewsets.ViewSet):
    # TODO: Cache retrive response to file
    authentication_classes = (TokenAuthentication,)
    permission_classes = (LangStringPermission,)
    lookup_url_kwarg = "pk"

    @extend_schema(request=None, responses=LanguageListSerializer)
    def list(self, request, version=None):
        languages = [{"code": code, "title": title} for code, title in settings.LANGUAGES]
        return response.Response(
            {
                "count": len(languages),
                "results": languages,
            }
        )

    @extend_schema(request=None, responses=LanguageRetriveSerializer)
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
    @extend_schema(request=LanguageBulkActionsSerializer, responses=LanguageBulkActionResponseSerializer)
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
        existing_string_keys = {
            (page_name, key): id for page_name, key, id in lang_strings_qs.values_list("page_name", "key", "id")
        }

        new_strings: typing.List[String] = []
        to_update_strings: typing.List[String] = []
        deleted_string_ids: typing.List[int] = []
        changed_strings: typing.Dict[typing.Tuple[str, str], typing.Dict] = {}

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
            }
            if action == LanguageBulkActionSerializer.SET:
                if (page_name, key) in existing_string_keys:
                    changed_strings[(page_name, key)] = value_meta
                else:
                    new_strings.append(String(language=lang, page_name=page_name, key=key, **value_meta))
            elif action == LanguageBulkActionSerializer.DELETE:
                if (page_name, key) in existing_string_keys:
                    deleted_string_ids.append(existing_string_keys[(page_name, key)])

        if len(new_strings):
            new_strings = String.objects.bulk_create(new_strings)
        if len(deleted_string_ids):
            String.objects.filter(id__in=deleted_string_ids).delete()
        if len(changed_strings):
            to_update_strings_qs = lang_strings_qs.filter(key__in={key for _, key in changed_strings}).all()
            for string in to_update_strings_qs:
                if (string.page_name, string.key) not in changed_strings:
                    continue
                string.value = changed_strings[(string.page_name, string.key)]["value"]
                string.hash = changed_strings[(string.page_name, string.key)]["hash"]
                to_update_strings.append(string)
            String.objects.bulk_update(to_update_strings, ["value", "hash"])

        return response.Response(
            {
                "new_strings": StringSerializer(new_strings, many=True).data,
                "updated_strings": StringSerializer(to_update_strings, many=True).data,
                "deleted_string_ids": deleted_string_ids,
            }
        )
