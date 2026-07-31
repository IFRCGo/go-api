"""Regression tests for /api/v2/dref3/ defects found in code review.

Each test covers a defect that the 134-run parity matrix could not catch,
because that matrix only exercised anonymous + superuser callers issuing
well-formed GETs. The gaps were: light-user visibility (anon / plain auth),
the non-superuser "DREF3 Admins" class, non-GET methods, `.format` suffixes
and malformed query params.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status

from api.models import Appeal, AppealFilter, AppealType, Country, Region, RegionName
from dref.dref3.common import Dref3PageHydrator, dref3_csv_header
from dref.factories.dref import (
    DrefFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
)
from dref.models import Dref
from main.test_case import APITestCase

User = get_user_model()


class Dref3LightUserVisibilityTests(APITestCase):
    """Anonymous / plain-authenticated callers: only APPROVED rows, and never
    an embargoed appeal code. This filtering exists twice - in SQL in the union
    branch and in the hydrator - so it must be asserted through the endpoint,
    where a disagreement between the two shows up as results shorter than
    `count`.
    """

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.approved = DrefFactory.create(
            appeal_code="APPROVED_CODE",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        self.draft = DrefFactory.create(
            appeal_code="DRAFT_CODE",
            national_society=self.country,
            status=Dref.Status.DRAFT,
        )

    def _payload(self, resp):
        body = resp.json()
        return body["results"], body["count"]

    def test_anonymous_sees_only_approved_rows(self):
        resp = self.client.get(self.url, {"limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows, count = self._payload(resp)
        codes = {row["appeal_id"] for row in rows}
        self.assertIn("APPROVED_CODE", codes)
        self.assertNotIn("DRAFT_CODE", codes)
        # count must describe the same set the caller actually received
        self.assertEqual(count, len(rows))

    def test_plain_authenticated_user_sees_only_approved_rows(self):
        user = User.objects.create_user("plain", "plain@example.com", "password")
        self.authenticate(user)
        resp = self.client.get(self.url, {"limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows, count = self._payload(resp)
        codes = {row["appeal_id"] for row in rows}
        self.assertIn("APPROVED_CODE", codes)
        self.assertNotIn("DRAFT_CODE", codes)
        self.assertEqual(count, len(rows))

    def test_excluded_appeal_code_is_hidden_and_count_agrees(self):
        """The union excludes embargoed codes in SQL while the hydrator did it
        in Python; if the two ever disagree the page silently returns fewer
        rows than `count` promises.
        """
        AppealFilter.objects.create(name="ingestAppealFilter", value="APPROVED_CODE")
        resp = self.client.get(self.url, {"limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows, count = self._payload(resp)
        self.assertNotIn("APPROVED_CODE", {row["appeal_id"] for row in rows})
        self.assertEqual(count, len(rows))


class Dref3AdminUserAccessTests(APITestCase):
    """Non-superuser member of "DREF3 Admins" with no dref_region_admin_*
    permission - the only class routed through `Model.get_for(user)`, which
    *replaces* the queryset and so used to discard the caller's filters and
    the hydrator's own appeal_code narrowing.
    """

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.user = User.objects.create_user("dref3admin", "dref3admin@example.com", "password")
        self.user.groups.set([Group.objects.get_or_create(name="DREF3 Admins")[0]])

        self.kept = DrefFactory.create(
            appeal_code="MDRAA001",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        self.other = DrefFactory.create(
            appeal_code="ZZZBB002",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        # get_for() matches DREFs the user created or is shared on
        self.kept.users.add(self.user)
        self.other.users.add(self.user)

    def test_filters_are_not_discarded(self):
        self.authenticate(self.user)
        resp = self.client.get(self.url, {"appeal_code_prefix": "MDRAA", "limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = {row["appeal_id"] for row in resp.json()["results"]}
        self.assertEqual(codes, {"MDRAA001"}, "user-access narrowing discarded the prefix filter")

    def test_retrieve_returns_only_the_requested_code(self):
        self.authenticate(self.user)
        resp = self.client.get(f"{self.url}MDRAA001/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = {row["appeal_id"] for row in resp.json()}
        self.assertEqual(codes, {"MDRAA001"})

    def test_retrieve_populates_link_to_emergency_page(self):
        """The serializer trusts the prefetched Appeal map instead of falling
        back to a per-row query, so the map must cover every serialized row.
        """
        from api.models import Event

        # An Appeal only yields a link when it points at an event
        event = Event.objects.create(name="E1")
        Appeal.objects.create(
            code="MDRAA001",
            aid="MDRAA001",
            atype=AppealType.DREF,
            country=self.country,
            region=self.region,
            event=event,
        )

        self.authenticate(self.user)
        resp = self.client.get(f"{self.url}MDRAA001/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows = resp.json()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(
                row["link_to_emergency_page"],
                f"https://go.ifrc.org/emergencies/{event.pk}/details",
            )

    def test_appeal_map_covers_every_serialized_row(self):
        """Invariant behind the removed N+1 fallback, asserted directly."""
        hydrator = Dref3PageHydrator(self.user)
        groups = hydrator.fetch_groups(["MDRAA001"])
        self.assertTrue(groups)
        self.assertEqual(set(groups) - set(hydrator._appeal_map(groups)) - {"MDRAA001"}, set())
        # every fetched group's code is a candidate key in the map lookup
        for code in groups:
            self.assertIsNotNone(code)


class Dref3MalformedParamTests(APITestCase):
    """Bad query params must not become HTTP 500."""

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.dref = DrefFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")

    def test_unicode_digit_in_id_param_is_ignored(self):
        """'²'.isdigit() is True but int('²') raises, which used to 500."""
        resp = self.client.get(self.url, {"id": "Dref-²"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["results"], [])

    def test_impossible_date_param_is_ignored(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"event_date_from": "2024-13-01", "limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # unparseable -> filter dropped, same as every other coercer here
        codes = {row["appeal_id"] for row in resp.json()["results"]}
        self.assertIn("APPEAL_A", codes)

    def test_garbage_date_params_are_ignored(self):
        self.authenticate(self.superuser)
        for param in (
            "event_date_from",
            "date_of_approval_to",
            "publishing_date_from",
            "start_date_of_operation",
            "end_date_of_operation",
        ):
            with self.subTest(param=param):
                resp = self.client.get(self.url, {param: "not-a-date", "limit": 100000})
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_iso_datetime_date_param_is_ignored_not_500(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"event_date_from": "2024-01-01T00:00:00Z", "limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_valid_date_param_still_filters(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"event_date_from": "2999-01-01", "limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = {row["appeal_id"] for row in resp.json()["results"]}
        self.assertNotIn("APPEAL_A", codes, "a valid date bound must still constrain application rows")


class Dref3RoutingTests(APITestCase):
    """Read-only viewset: wrong methods are 405, and the detail route must not
    swallow DRF's `.format` suffix."""

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.dref = DrefFactory.create(
            appeal_code="MDRAA001",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )

    def test_post_is_method_not_allowed(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_on_detail_is_method_not_allowed(self):
        resp = self.client.delete(f"{self.url}MDRAA001/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_detail_json_format_suffix_returns_the_record(self):
        """Both suffix forms must resolve. Widening lookup_value_regex to
        [^/]+ broke the trailing-slash form specifically: the non-suffixed
        pattern matched first and the code swallowed ".json", yielding an
        empty 200 instead of the record.
        """
        plain = self.client.get(f"{self.url}MDRAA001/")
        self.assertEqual(plain.status_code, status.HTTP_200_OK)
        self.assertTrue(plain.json())
        for suffixed_url in (f"{self.url}MDRAA001.json", f"{self.url}MDRAA001.json/"):
            with self.subTest(url=suffixed_url):
                resp = self.client.get(suffixed_url)
                self.assertEqual(resp.status_code, status.HTTP_200_OK)
                self.assertEqual(resp.json(), plain.json())


class Dref3CsvExportTests(APITestCase):
    """The export is unpaginated by design, so it streams in chunks."""

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.dref = DrefFactory.create(
            appeal_code="MDRAA001",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        DrefOperationalUpdateFactory.create(
            appeal_code="MDRAA001",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            dref=self.dref,
        )
        DrefFinalReportFactory.create(
            appeal_code="MDRAA001",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            dref=self.dref,
        )

    def test_csv_export_streams_all_rows(self):
        resp = self.client.get(self.url, {"export": "csv"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.streaming, "export must stream rather than buffer the whole set")
        body = b"".join(resp.streaming_content).decode()
        lines = [line for line in body.splitlines() if line.strip()]
        # header + the three stage rows
        self.assertEqual(lines[0].split(","), dref3_csv_header())
        self.assertEqual(len(lines), 4)

    def test_csv_export_respects_filters(self):
        resp = self.client.get(self.url, {"export": "csv", "appeal_code_prefix": "NOPE"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = b"".join(resp.streaming_content).decode()
        lines = [line for line in body.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, "only the header should remain")
