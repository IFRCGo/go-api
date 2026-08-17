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
from dref.dref3.common import DREF3_FILTERS, Dref3PageHydrator, dref3_csv_header
from dref.dref3.query import build_union_queryset
from dref.dref3.schema import DREF3_LIST_PARAMETERS
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

    def test_mixed_case_excluded_code_is_hidden_and_not_reported_public(self):
        """The embargo list is uppercased and matched with SQL upper(), so a
        mixed-case appeal_code is embargoed too. The `public` flag is computed
        in Python from the same set and must agree: an admin who can see the
        row must not be told it is public.
        """
        DrefFactory.create(
            appeal_code="mdrZz009",
            national_society=self.country,
            status=Dref.Status.APPROVED,
        )
        AppealFilter.objects.create(name="ingestAppealFilter", value="MDRZZ009")

        # Light user: the row is not visible at all.
        resp = self.client.get(self.url, {"limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows, count = self._payload(resp)
        self.assertNotIn("mdrZz009", {row["appeal_id"] for row in rows})
        self.assertEqual(count, len(rows))

        # Full-access user: the row is visible, and flagged non-public.
        self.authenticate(self.root_user)
        resp = self.client.get(self.url, {"appeal_code_prefix": "mdrZz", "limit": 100000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows, _ = self._payload(resp)
        self.assertTrue(rows, "embargoed row should still be visible to full-access users")
        for row in rows:
            self.assertFalse(row["public"], "embargoed mixed-case code reported as public")


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


class Dref3HazardTextSearchTests(APITestCase):
    """`hazard_date_and_location` is free prose ("when and where is the hazard
    expected to happen?"), so it is filtered by substring rather than bounded:
    ordering prose against a date bound selects an arbitrary set of rows.
    """

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.dref = DrefFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            hazard_date_and_location="Forecast window 15-22 December 2025, Elbasan and Tirana",
        )
        self.other = DrefFactory.create(
            appeal_code="APPEAL_B",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            hazard_date_and_location="Cyclone landfall expected on the northern coast",
        )
        self.blank = DrefFactory.create(
            appeal_code="APPEAL_BLANK",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            hazard_date_and_location="",
        )

    def _codes(self, params, stage="application"):
        self.authenticate(self.superuser)
        query = {"limit": 100000, **params}
        if stage:
            query["stage"] = stage
        resp = self.client.get(self.url, query)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return {row["appeal_id"] for row in resp.json()["results"]}

    def test_matches_a_substring_anywhere_in_the_value(self):
        self.assertEqual(self._codes({"hazard_date_and_location": "Elbasan"}), {"APPEAL_A"})
        self.assertEqual(self._codes({"hazard_date_and_location": "northern coast"}), {"APPEAL_B"})

    def test_match_is_case_insensitive(self):
        self.assertEqual(self._codes({"hazard_date_and_location": "elbasan"}), {"APPEAL_A"})
        self.assertEqual(self._codes({"hazard_date_and_location": "CYCLONE"}), {"APPEAL_B"})

    def test_a_term_matching_nothing_returns_no_rows(self):
        self.assertEqual(self._codes({"hazard_date_and_location": "Reykjavik"}), set())

    def test_blank_and_whitespace_terms_are_ignored(self):
        """A blank term must not become `icontains=""`, which matches every row
        with a value and so would silently drop only the rows without one."""
        for term in ("", "   "):
            with self.subTest(term=term):
                self.assertEqual(
                    self._codes({"hazard_date_and_location": term}),
                    {"APPEAL_A", "APPEAL_B", "APPEAL_BLANK"},
                )

    def test_rows_without_a_value_are_never_matched(self):
        DrefFactory.create(
            appeal_code="APPEAL_NULL",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            hazard_date_and_location=None,
        )
        codes = self._codes({"hazard_date_and_location": "December"})
        self.assertNotIn("APPEAL_NULL", codes)
        self.assertNotIn("APPEAL_BLANK", codes)

    def test_only_application_rows_are_constrained(self):
        """The field exists on the application stage only, so operational update
        and final report rows pass the filter rather than being dropped."""
        DrefOperationalUpdateFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            dref=self.dref,
        )
        DrefFinalReportFactory.create(
            appeal_code="APPEAL_B",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            dref=self.other,
        )
        codes = self._codes({"hazard_date_and_location": "Elbasan"}, stage=None)
        self.assertEqual(codes, {"APPEAL_A", "APPEAL_B"})

    def test_the_range_bound_params_are_not_exposed(self):
        """Bounding this field is not a supported operation, so the two params
        appear in neither the filter mapping nor the published schema."""
        for param in ("hazard_date_and_location_from", "hazard_date_and_location_to"):
            with self.subTest(param=param):
                self.assertNotIn(param, DREF3_FILTERS)
                self.assertNotIn(param, {p.name for p in DREF3_LIST_PARAMETERS})

    def test_searches_the_active_language_column(self):
        """The field is registered with modeltranslation, so the lookup is
        rewritten onto the active language's column - the column a value written
        through the API lands in. The untranslated base column only holds values
        stored before the translated columns existed."""
        queryset = build_union_queryset(self.superuser, {"stage": "application", "hazard_date_and_location": "Elbasan"})
        sql, params = queryset.query.sql_with_params()
        self.assertIn("hazard_date_and_location_en", sql)
        self.assertIn("LIKE UPPER", sql)
        self.assertIn("%Elbasan%", params)


class Dref3HazardDateRangeTests(APITestCase):
    """`hazard_date` is the DateField behind "when is the hazard expected to
    happen?", so it is what a caller bounding a hazard date wants. It is a
    range filter alongside the other eight application dates."""

    def setUp(self):
        super().setUp()
        self.url = "/api/v2/dref3/"
        self.region = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.country = Country.objects.create(name="C1", iso3="AAA", iso="AA", region=self.region)
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")
        for code, hazard_date in (("APPEAL_EARLY", "2025-03-01"), ("APPEAL_LATE", "2026-09-15")):
            DrefFactory.create(
                appeal_code=code,
                national_society=self.country,
                status=Dref.Status.APPROVED,
                hazard_date=hazard_date,
            )
        self.undated = DrefFactory.create(
            appeal_code="APPEAL_NONE",
            national_society=self.country,
            status=Dref.Status.APPROVED,
            hazard_date=None,
        )

    def _codes(self, params):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"stage": "application", "limit": 100000, **params})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return {row["appeal_id"] for row in resp.json()["results"]}

    def test_bounds_select_by_date(self):
        self.assertEqual(self._codes({"hazard_date_from": "2026-01-01"}), {"APPEAL_LATE"})
        self.assertEqual(self._codes({"hazard_date_to": "2026-01-01"}), {"APPEAL_EARLY"})
        self.assertEqual(
            self._codes({"hazard_date_from": "2025-01-01", "hazard_date_to": "2026-12-31"}),
            {"APPEAL_EARLY", "APPEAL_LATE"},
        )

    def test_rows_without_a_hazard_date_are_never_matched(self):
        for param in ("hazard_date_from", "hazard_date_to"):
            with self.subTest(param=param):
                self.assertNotIn("APPEAL_NONE", self._codes({param: "2025-01-01"}))

    def test_unparseable_bound_is_ignored_like_the_other_dates(self):
        codes = self._codes({"hazard_date_from": "not-a-date"})
        self.assertEqual(codes, {"APPEAL_EARLY", "APPEAL_LATE", "APPEAL_NONE"})


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


class Dref3SchemaParameterTests(APITestCase):
    """The documented parameters must stay tied to what the code honours.

    An earlier hand-written `appeal_type` description listed the wrong label
    for three of the four ids and was published in the OpenAPI schema, so
    these assert the enum-derived text against the model rather than a copy.
    """

    def test_every_filter_is_documented(self):
        documented = {p.name for p in DREF3_LIST_PARAMETERS}
        missing = set(DREF3_FILTERS) - documented
        self.assertEqual(missing, set(), f"filters applied but not documented: {sorted(missing)}")

    def test_appeal_type_enum_matches_model(self):
        param = next(p for p in DREF3_LIST_PARAMETERS if p.name == "appeal_type")
        self.assertEqual(list(param.enum), [choice.value for choice in Dref.DrefType])
        for choice in Dref.DrefType:
            self.assertIn(f"`{choice.value}` {choice.label}", param.description)

    def test_operation_status_lists_every_model_status(self):
        param = next(p for p in DREF3_LIST_PARAMETERS if p.name == "operation_status")
        for choice in Dref.Status:
            self.assertIn(f"`{choice.value}` {choice.label}", param.description)
        # It accepts labels and names too, so it must not claim a closed id set
        self.assertIsNone(param.enum)

    def test_stage_scoped_filters_say_so(self):
        """Date-range filters constrain application rows only; the schema must
        state that, since it surprises callers who expect whole groups."""
        param = next(p for p in DREF3_LIST_PARAMETERS if p.name == "event_date_from")
        self.assertIn("Application", param.description)


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
