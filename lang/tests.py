import unittest
from unittest import mock

from django.test import override_settings
from django.conf import settings
from django.core import management
from django.contrib.auth.models import User, Permission
from main.test_case import APITestCase

from lang.translation import IfrcTranslator

from .serializers import LanguageBulkActionSerializer
from .models import String


class LangTest(APITestCase):
    def setUp(self):
        super().setUp()
        management.call_command("make_permissions")

    def test_list_languages(self):
        self.authenticate(self.user)
        resp = self.client.get("/api/v2/language/")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp["results"]), len(settings.LANGUAGES))
        self.assertEqual(j_resp["count"], len(settings.LANGUAGES))

    def test_list_strings(self):
        language = settings.LANGUAGES[0][0]
        current_strings_count = String.objects.filter(language=language).count()
        String.objects.create(
            language=language, key="random-key-for-language-test1", value="Random value", hash="random hash"
        )
        self.authenticate(self.user)
        resp = self.client.get(f"/api/v2/language/{language}/")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp["strings"]), current_strings_count + 1)

    def test_page_number_filter(self):
        language = settings.LANGUAGES[0][0]
        String.objects.create(
            language=language,
            key="random-key-for-language-test1",
            value="Random value",
            hash="random hash",
            page_name="home",
        )
        String.objects.create(
            language=language,
            key="random-key-for-language-test2",
            value="Random value",
            hash="random hash",
            page_name="risk-module",
        )
        String.objects.create(
            language=language,
            key="random-key-for-language-test3",
            value="Random value",
            hash="random hash",
            page_name="dref",
        )
        self.authenticate(self.user)
        resp = self.client.get(f"/api/v2/language/{language}/?page_name=home,dref")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp["strings"]), 2)

        resp = self.client.get(f"/api/v2/language/{language}/?page_name=common")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp["strings"]), 0)

        resp = self.client.get(f"/api/v2/language/{language}/?page_name=dref,common")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp["strings"]), 1)

    def test_bulk_action(self):
        language = settings.LANGUAGES[0][0]
        string_1 = {"key": "new-string-101", "value": "New Value 101", "hash": "new-hash-101", "page_name": "dref"}
        string_2 = {"key": "new-string-102", "value": "New Value 102", "hash": "new-hash-102", "page_name": "risk-module"}
        string_3 = {"key": "new-string-103", "value": "New Value 103", "hash": "new-hash-103"}
        data = {
            "actions": [
                {
                    "action": LanguageBulkActionSerializer.SET,
                    **string_1,
                },
                {
                    "action": LanguageBulkActionSerializer.SET,
                    **string_2,
                },
                {
                    "action": LanguageBulkActionSerializer.SET,
                    **string_3,
                },
            ],
        }

        self.authenticate(self.root_user)
        resp = self.client.post(f"/api/v2/language/{language}/bulk-action/", data, format="json")
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)

        first_string = j_resp["new_strings"][0]
        second_string = j_resp["new_strings"][1]
        third_string = j_resp["new_strings"][2]
        first_string.pop("id")
        second_string.pop("id")
        third_string.pop("id")
        third_string.pop("page_name")
        self.assertEqual(first_string, {**string_1, "language": language})
        self.assertEqual(second_string, {**string_2, "language": language})
        self.assertEqual(third_string, {**string_3, "language": language})

        string_2["value"] = "updated value 101"
        data = {
            "actions": [
                {"action": LanguageBulkActionSerializer.DELETE, **string_1},
                {"action": LanguageBulkActionSerializer.SET, **string_2},
            ],
        }
        resp = self.client.post(f"/api/v2/language/{language}/bulk-action/", data, format="json")
        j_resp = resp.json()

        first_string_key = j_resp["deleted_strings_keys"][0]
        second_string = j_resp["updated_strings"][0]
        second_string.pop("id")
        self.assertEqual(second_string, {**string_2, "language": language})
        self.assertEqual(first_string_key, string_1["key"])

    def test_user_me(self):
        user = User.objects.create_user(
            username="user@test.com",
            first_name="User",
            last_name="Toot",
            password="user123",
            email="user@test.com",
        )

        self.authenticate(user)

        resp = self.client.get("/api/v2/user/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data["lang_permissions"],
            {
                "en": False,
                "es": False,
                "ar": False,
                "fr": False,
            },
        )

        # Change permission and check
        user.user_permissions.add(
            Permission.objects.filter(codename="lang__string__maintain__en").first(),
            Permission.objects.filter(codename="lang__string__maintain__ar").first(),
        )

        resp = self.client.get("/api/v2/user/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data["lang_permissions"],
            {
                "en": True,
                "es": False,
                "ar": True,
                "fr": False,
            },
        )

        # For superuser all should be true
        self.authenticate(self.root_user)
        resp = self.client.get("/api/v2/user/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data["lang_permissions"],
            {
                "en": True,
                "es": True,
                "ar": True,
                "fr": True,
            },
        )

    def test_lang_api_permissions(self):
        user = User.objects.create_user(
            username="user@test.com",
            first_name="User",
            last_name="Toot",
            password="user123",
            email="user@test.com",
        )

        language = settings.LANGUAGES[0][0]
        string_1 = {
            "key": "new-string-101",
            "value": "New Value 101",
            "hash": "new-hash-101",
        }
        string_2 = {
            "key": "new-string-102",
            "value": "New Value 102",
            "hash": "new-hash-102",
        }
        data = {
            "actions": [
                {"action": LanguageBulkActionSerializer.SET, **string_1},
                {"action": LanguageBulkActionSerializer.SET, **string_2},
            ],
        }

        self.authenticate(user)
        resp = self.client.post(f"/api/v2/language/{language}/bulk-action/", data, format="json")
        self.assertEqual(resp.status_code, 403)

        user.user_permissions.add(
            Permission.objects.filter(codename=f"lang__string__maintain__{language}").first(),
        )

        self.authenticate(user)
        resp = self.client.post(f"/api/v2/language/{language}/bulk-action/", data, format="json")
        self.assertEqual(resp.status_code, 200)


class TranslatorMockTest(unittest.TestCase):

    @mock.patch('lang.translation.requests')
    def test_ifrc_translator(self, requests_mock):
        # Simple mock test where we define what the expected response is from provider
        requests_mock.post.return_value.json.return_value = [{
            "detectedLanguage": {"language": "en", "score": 1},
            "translations": [{"text": "Hola", "to": "es"}]
        }]

        # Without valid settings provided
        for settings_params in [
            dict(),
            dict(
                IFRC_TRANSLATION_GET_API_KEY='dummy-api-param-key',
                IFRC_TRANSLATION_HEADER_API_KEY='dummy-api-header-key',
            ),
            dict(IFRC_TRANSLATION_HEADER_API_KEY='dummy-api-header-key'),
        ]:
            with override_settings(
                AUTO_TRANSLATION_TRANSLATOR='lang.translation.IfrcTranslator',
                **settings_params,
            ):
                with self.assertRaises(Exception):
                    IfrcTranslator()

        # With valid settings provided
        with override_settings(
            AUTO_TRANSLATION_TRANSLATOR='lang.translation.IfrcTranslator',
            IFRC_TRANSLATION_DOMAIN='http://example.org',
            IFRC_TRANSLATION_GET_API_KEY='dummy-api-param-key',
            IFRC_TRANSLATION_HEADER_API_KEY='dummy-api-header-key',
        ):
            # with settings.TESTING True
            ifrc_translator = IfrcTranslator()
            assert ifrc_translator.translate_text('hello', 'es') == 'hello translated to "es" using source language "None"'
            # with settings.TESTING False
            with override_settings(TESTING=False):
                assert ifrc_translator.translate_text('hello', 'es') == "Hola"
