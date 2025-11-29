from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from modeltranslation.utils import build_localized_fieldname

from api.factories.country import CountryFactory
from api.factories.region import RegionFactory
from deployments.factories.molnix_tag import MolnixTagFactory
from deployments.factories.user import UserFactory
from lang.serializers import TranslatedModelSerializerMixin
from main.test_case import APITestCase
from notifications.factories import (
    AlertSubscriptionFactory,
    HazardTypeFactory,
    SurgeAlertFactory,
)
from notifications.management.commands.ingest_alerts import categories, timeformat
from notifications.models import (
    AlertSubscription,
    HazardType,
    SurgeAlert,
    SurgeAlertStatus,
    SurgeAlertType,
)


class NotificationTestCase(APITestCase):

    def test_surge_translation(self):
        alerts = [
            [
                "FACT",  # atype
                "Information",  # category
                "Mozambique Tropical Storm DINEO",  # operation
                # message
                "Due to the very limited number of Portuguese and Spanish speakers in our roster, we would appreciate if you could please let us know your tentative availability, only in case you speak Portuguese and/or Spanish.",  # noqa: E501
                "2017-02-15",  # created_at: date
                "14:23",  # created_at: time
            ],
        ]

        surge_alerts = []
        surge_alerts_field_values = {}
        for alert in alerts:
            fields = {
                "atype": SurgeAlertType[alert[0].strip().upper()],
                "category": categories[alert[1].strip().lower()],
                "operation": alert[2].strip(),
                "message": alert[3].strip(),
                "deployment_needed": False,
                "is_private": True,
                "created_at": datetime.strptime(
                    "%s:%s" % (alert[4].strip(), alert[5].strip()),
                    timeformat,
                ).replace(tzinfo=timezone.utc),
            }
            surge_alert = SurgeAlert(**fields)
            surge_alert.save()
            surge_alerts.append(surge_alert)
            surge_alerts_field_values[surge_alert.pk] = fields

        # Trigger translation
        with self.capture_on_commit_callbacks(execute=True):
            TranslatedModelSerializerMixin.trigger_field_translation_in_bulk(SurgeAlert, surge_alerts)

        for surge_alert in surge_alerts:
            surge_alert.refresh_from_db()
            for field in ["operation", "message"]:
                for lang, _ in settings.LANGUAGES:
                    original_value = surge_alerts_field_values[surge_alert.pk][field]
                    self.assertEqual(
                        getattr(surge_alert, build_localized_fieldname(field, lang)),
                        self.aws_translator._fake_translation(original_value, lang, "en") if lang != "en" else original_value,
                    )


class SurgeAlertFilteringTest(APITestCase):
    def test_filtering(self):
        region_1, region_2 = RegionFactory.create_batch(2)
        country_1 = CountryFactory.create(iso3="ATL", region=region_1)
        country_2 = CountryFactory.create(iso3="NPT", region=region_2)

        molnix_tag_1 = MolnixTagFactory.create(name="OP-6700")
        molnix_tag_2 = MolnixTagFactory.create(name="L-FRA")
        molnix_tag_3 = MolnixTagFactory.create(name="AMER")

        SurgeAlertFactory.create(
            message="CEA Coordinator, Floods, Atlantis",
            country=country_1,
            molnix_status=SurgeAlertStatus.OPEN,
            molnix_tags=[molnix_tag_1, molnix_tag_2],
        )
        SurgeAlertFactory.create(
            message="WASH Coordinator, Earthquake, Neptunus",
            country=country_2,
            molnix_status=SurgeAlertStatus.STOOD_DOWN,
            molnix_tags=[molnix_tag_1, molnix_tag_3],
        )

        # we have 2 SurgeAlerts with 2 different Countries: A, B
        # Filtering for X, B gives 1; filtering for A, B gives both results.

        def _fetch(filters):
            return self.client.get("/api/v2/surge_alert/", filters).json()

        def _to_csv(*items):
            return ",".join([str(i) for i in items])

        response = _fetch(dict(country__iso3__in="AAA,NPT"))
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["molnix_tags"][0]["name"], "OP-6700")

        response = _fetch(dict(country__iso3__in="ATL,NPT"))
        self.assertEqual(response["count"], 2)
        self.assertEqual(
            {
                response["results"][0]["molnix_tags"][0]["name"],
                response["results"][0]["molnix_tags"][1]["name"],
                response["results"][1]["molnix_tags"][0]["name"],
                response["results"][1]["molnix_tags"][1]["name"],
            },
            {"OP-6700", "L-FRA", "AMER"},
        )

        # we have 2 SurgeAlerts with MolnixTags A, B and A, C.
        # Filtering for A, B, C gives both. Filtering for only B or C gives 1.

        # filtering by molnix_tags

        response = _fetch(
            dict(
                country__iso3__in="ATL,NPT",
                molnix_tags=_to_csv(molnix_tag_2.id),
            )
        )
        self.assertEqual(response["count"], 1)

        response = _fetch(
            dict(
                country__iso3__in="ATL,NPT",
                molnix_tags=_to_csv(molnix_tag_1.id, molnix_tag_2.id, molnix_tag_3.id),
            )
        )
        self.assertEqual(response["count"], 2)

        response = _fetch(
            dict(
                country__iso3__in="ATL,NPT",
                molnix_tag_names=_to_csv("AMER"),
            )
        )
        self.assertEqual(response["count"], 1)

        response = _fetch(
            dict(
                country__iso3__in="ATL,NPT",
                molnix_tag_names=_to_csv("OP-6700", "L-FRA", "AMER"),
            )
        )
        self.assertEqual(response["count"], 2)

        SurgeAlertFactory.create_batch(5, molnix_status=SurgeAlertStatus.CLOSED)

        response = _fetch(
            dict(
                molnix_status=SurgeAlertStatus.OPEN,
            )
        )
        self.assertEqual(response["count"], 1)

        response = _fetch(
            dict(
                molnix_status=SurgeAlertStatus.CLOSED,
            )
        )
        self.assertEqual(response["count"], 5)

    def test_surge_alert_status(self):
        def _to_csv(*items):
            return ",".join([str(i) for i in items])

        region_1, region_2 = RegionFactory.create_batch(2)
        country_1 = CountryFactory.create(iso3="ATL", region=region_1)
        country_2 = CountryFactory.create(iso3="NPT", region=region_2)

        molnix_tag_1 = MolnixTagFactory.create(name="OP-6700")
        molnix_tag_2 = MolnixTagFactory.create(name="L-FRA")
        molnix_tag_3 = MolnixTagFactory.create(name="AMER")

        SurgeAlertFactory.create(
            message="CEA Coordinator, Floods, Atlantis",
            country=country_1,
            molnix_status=SurgeAlertStatus.OPEN,
            molnix_tags=[molnix_tag_1, molnix_tag_2],
            opens=timezone.now() - timedelta(days=2),
            closes=timezone.now() + timedelta(days=5),
        )
        SurgeAlertFactory.create(
            message="WASH Coordinator, Earthquake, Neptunus",
            country=country_2,
            molnix_status=SurgeAlertStatus.CLOSED,
            molnix_tags=[molnix_tag_1, molnix_tag_3],
            opens=timezone.now() - timedelta(days=2),
            closes=timezone.now() - timedelta(days=1),
        )
        SurgeAlertFactory.create(
            message="New One",
            country=country_2,
            molnix_status=SurgeAlertStatus.STOOD_DOWN,
            molnix_tags=[molnix_tag_1, molnix_tag_3],
        )

        def _fetch(filters):
            return self.client.get("/api/v2/surge_alert/", filters).json()

        response = _fetch(dict({"molnix_status": SurgeAlertStatus.OPEN}))

        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["molnix_status"], SurgeAlertStatus.OPEN)

        response = _fetch(dict({"molnix_status": SurgeAlertStatus.CLOSED}))
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["molnix_status"], SurgeAlertStatus.CLOSED)

        response = _fetch(dict({"molnix_status": _to_csv(SurgeAlertStatus.STOOD_DOWN, SurgeAlertStatus.OPEN)}))
        self.assertEqual(response["count"], 2)
        self.assertEqual(response["results"][0]["molnix_status"], SurgeAlertStatus.STOOD_DOWN)


class AlertSubscriptionTestCase(APITestCase):

    def setUp(self):
        self.user1 = UserFactory.create(email="testuser1@com")
        self.user2 = UserFactory.create(email="testuser2@com")

        self.region = RegionFactory.create(name=2)
        self.regions = RegionFactory.create_batch(3)
        self.countries = CountryFactory.create_batch(2)

        self.country = CountryFactory.create(
            name="Nepal",
            iso3="NLP",
            iso="NP",
            region=self.region,
        )

        self.country_1 = CountryFactory.create(
            name="Philippines",
            iso3="PHL",
            iso="PH",
            region=self.region,
        )
        self.hazard_type1 = HazardTypeFactory.create(type=HazardType.Type.EARTHQUAKE)
        self.hazard_type2 = HazardTypeFactory.create(type=HazardType.Type.FLOOD)

        self.alert_subscription = AlertSubscriptionFactory.create(
            user=self.user1,
            countries=self.countries,
            regions=[self.region],
            hazard_types=[self.hazard_type1, self.hazard_type2],
        )

    def test_list_retrieve_subscription(self):
        url = "/api/v2/alert-subscription/"

        # Anonymous user cannot access list
        response = self.client.get(url)
        self.assert_401(response)

        # Authenticated user can list
        self.authenticate(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Retrieve detail
        url = f"/api/v2/alert-subscription/{self.alert_subscription.id}/"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["user"], self.user1.id)

    # Test Create Subscription
    def test_create_subscription(self):

        data = {
            "user": self.user1.id,
            "countries": [self.country.id, self.country_1.id],
            "regions": [self.region.id],
            "hazard_types": [self.hazard_type1.id, self.hazard_type2.id],
            "alert_per_day": AlertSubscription.AlertPerDay.TEN,
            "source": AlertSubscription.AlertSource.MONTANDON,
        }
        url = "/api/v2/alert-subscription/"
        self.authenticate(self.user1)
        response = self.client.post(url, data=data, format="json")
        self.assert_201(response)
        subscription = AlertSubscription.objects.get(id=response.data["id"])
        self.assertEqual(subscription.user, self.user1)
        self.assertEqual(subscription.countries.count(), 2)
        self.assertEqual(subscription.regions.count(), 1)
        self.assertEqual(subscription.hazard_types.count(), 2)
        self.assertEqual(subscription.alert_per_day, AlertSubscription.AlertPerDay.TEN)

    # Test Update
    def test_update_subscription(self):

        url = f"/api/v2/alert-subscription/{self.alert_subscription.id}/"
        data = {
            "countries": [self.country_1.id],
            "alert_per_day": AlertSubscription.AlertPerDay.UNLIMITED,
        }
        self.authenticate(self.user1)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)
        self.alert_subscription.refresh_from_db()
        self.assertEqual(self.alert_subscription.countries.first().id, self.country_1.id)
        self.assertEqual(self.alert_subscription.alert_per_day, AlertSubscription.AlertPerDay.UNLIMITED)
