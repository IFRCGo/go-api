from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status

from api.models import Country, Region, RegionName
from dref.factories.dref import (
    DrefFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
)
from dref.models import Dref
from main.test_case import APITestCase

User = get_user_model()


class Dref3FilterTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.url = "/api/v2/dref3/"
        self.region1 = Region.objects.create(name=RegionName.AFRICA, label="Africa")
        self.region2 = Region.objects.create(name=RegionName.AMERICAS, label="Americas")
        self.country1 = Country.objects.create(name="Country1", iso3="C11", iso="C1", region=self.region1)
        self.country2 = Country.objects.create(name="Country2", iso3="C22", iso="C2", region=self.region2)
        today = datetime.utcnow().date()
        self.dref_a = DrefFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country1,
            type_of_dref=Dref.DrefType.RESPONSE,
            date_of_approval=today - timedelta(days=5),
            end_date=today + timedelta(days=10),
            status=Dref.Status.DRAFT,
        )
        self.dref_b = DrefFactory.create(
            appeal_code="APPEAL_B",
            national_society=self.country2,
            type_of_dref=Dref.DrefType.IMMINENT,
            date_of_approval=today - timedelta(days=5),
            end_date=today + timedelta(days=20),
            status=Dref.Status.DRAFT,
        )
        self.op_a1 = DrefOperationalUpdateFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country1,
            type_of_dref=Dref.DrefType.RESPONSE,
            new_operational_start_date=today - timedelta(days=3),
            new_operational_end_date=today + timedelta(days=7),
            status=Dref.Status.DRAFT,
            dref=self.dref_a,
        )
        self.op_b1 = DrefOperationalUpdateFactory.create(
            appeal_code="APPEAL_B",
            national_society=self.country2,
            type_of_dref=Dref.DrefType.IMMINENT,
            new_operational_start_date=today - timedelta(days=2),
            new_operational_end_date=today + timedelta(days=9),
            status=Dref.Status.DRAFT,
            dref=self.dref_b,
        )
        self.final_a = DrefFinalReportFactory.create(
            appeal_code="APPEAL_A",
            national_society=self.country1,
            type_of_dref=Dref.DrefType.RESPONSE,
            operation_start_date=today - timedelta(days=15),
            operation_end_date=today - timedelta(days=1),
            status=Dref.Status.DRAFT,
            dref=self.dref_a,
        )

    def _get_codes(self, response):
        return {row["appeal_id"] for row in response.json()}

    def test_region_filter(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"region": self.region1.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert "APPEAL_A" in codes and "APPEAL_B" not in codes

    def test_country_iso3_filter(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"country_iso3": "C22"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert "APPEAL_B" in codes and "APPEAL_A" not in codes

    def test_appeal_type_filter(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"appeal_type": Dref.DrefType.IMMINENT})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert codes == {"APPEAL_B"}

    def test_operation_status_filter(self):
        self.authenticate(self.superuser)
        self.dref_a.status = Dref.Status.APPROVED
        self.dref_a.save(update_fields=["status"])
        resp = self.client.get(self.url, {"operation_status": Dref.Status.APPROVED})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert "APPEAL_A" in codes and "APPEAL_B" not in codes

    def test_stage_application(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"stage": "application"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        assert all(row["stage"] == "Application" for row in resp.json())

    def test_stage_operational_update(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"stage": "operational_update"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        assert all(row["stage"].startswith("Operational Update") for row in resp.json())

    def test_stage_final_report(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"stage": "final_report"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        assert all(row["stage"] == "Final Report" for row in resp.json())

    def test_filter_by_appeal_id(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"appeal_id": self.dref_a.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert codes == {"APPEAL_A"}

    def test_operation_start_end_filters(self):
        self.authenticate(self.superuser)
        resp = self.client.get(
            self.url,
            {
                "start_date_of_operation": (datetime.utcnow().date() - timedelta(days=7)).isoformat(),
                "end_date_of_operation": (datetime.utcnow().date() + timedelta(days=15)).isoformat(),
                "stage": "application",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = self._get_codes(resp)
        assert codes == {"APPEAL_A"}

    def test_pagination(self):
        self.authenticate(self.superuser)
        full = self.client.get(self.url)
        self.assertEqual(full.status_code, status.HTTP_200_OK)
        total = len(full.json())
        page1 = self.client.get(self.url, {"limit": 1, "offset": 0})
        self.assertEqual(page1.status_code, status.HTTP_200_OK)
        assert len(page1.json()) == 1
        if total > 1:
            page2 = self.client.get(self.url, {"limit": 1, "offset": 1})
            self.assertEqual(page2.status_code, status.HTTP_200_OK)
            assert len(page2.json()) == 1

    def test_export_csv(self):
        self.authenticate(self.superuser)
        resp = self.client.get(self.url, {"export": "csv", "stage": "application"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "text/csv")
        self.assertIn("attachment;", resp["Content-Disposition"])

    def test_numeric_id_filter_exact(self):
        self.authenticate(self.superuser)
        full_resp = self.client.get(self.url)
        self.assertEqual(full_resp.status_code, status.HTTP_200_OK)
        records = full_resp.json()
        self.assertGreater(len(records), 0)
        target_id = records[0]["id"]
        resp = self.client.get(self.url, {"id": str(target_id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        filtered = resp.json()
        assert len(filtered) == 1
        assert filtered[0]["id"] == target_id

    def test_numeric_id_filter_multiple(self):
        self.authenticate(self.superuser)
        full_resp = self.client.get(self.url)
        self.assertEqual(full_resp.status_code, status.HTTP_200_OK)
        records = full_resp.json()
        ids = [r["id"] for r in records][:2]
        if len(ids) < 2:
            self.skipTest("Need at least two records for multi-id filter test")
        resp = self.client.get(self.url, {"id": ",".join(str(i) for i in ids)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        filtered = resp.json()
        returned_ids = {r["id"] for r in filtered}
        assert returned_ids == set(ids)

    def test_status_display_labels(self):
        """Ensure status_display label matches underlying choice labels across aggregated records."""
        self.authenticate(self.superuser)
        # Mutate some statuses to have multiple labels represented
        self.dref_a.status = Dref.Status.APPROVED
        self.dref_a.save(update_fields=["status"])  # Approved -> "Approved"
        self.op_a1.status = Dref.Status.FINALIZED
        self.op_a1.save(update_fields=["status"])  # Finalized -> "Finalized"
        # Leave final report as Draft -> "Draft"
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows = resp.json()
        # Collect status_display values for appeal A
        appeal_a_statuses = {r["status_display"] for r in rows if r["appeal_id"] == "APPEAL_A"}
        # Expected labels
        assert {"Approved", "Finalized", "Draft"}.issubset(appeal_a_statuses)

    def test_is_latest_stage_flag_progression(self):
        """Verify is_latest_stage shifts to the newest approved stage only."""
        self.authenticate(self.superuser)
        # Initial: all DRAFT -> no latest stage
        resp_initial = self.client.get(f"/api/v2/dref3/{self.dref_a.appeal_code}/")
        self.assertEqual(resp_initial.status_code, status.HTTP_200_OK)
        data_initial = resp_initial.json()
        assert all(not row.get("is_latest_stage") for row in data_initial)

        # Approve application
        self.dref_a.status = Dref.Status.APPROVED
        self.dref_a.save(update_fields=["status"])
        resp_after_app = self.client.get(f"/api/v2/dref3/{self.dref_a.appeal_code}/")
        self.assertEqual(resp_after_app.status_code, status.HTTP_200_OK)
        data_after_app = resp_after_app.json()
        # Application should be latest stage
        latest_flags = [row.get("is_latest_stage") for row in data_after_app]
        assert any(latest_flags), "Expected one latest stage after application approval"
        app_rows = [row for row in data_after_app if row["stage"] == "Application"]
        assert app_rows and app_rows[0]["is_latest_stage"] is True

        # Approve operational update -> flag moves
        self.op_a1.status = Dref.Status.APPROVED
        self.op_a1.save(update_fields=["status"])
        resp_after_op = self.client.get(f"/api/v2/dref3/{self.dref_a.appeal_code}/")
        self.assertEqual(resp_after_op.status_code, status.HTTP_200_OK)
        data_after_op = resp_after_op.json()
        app_row = [r for r in data_after_op if r["stage"] == "Application"][0]
        op_row = [r for r in data_after_op if r["stage"].startswith("Operational Update")][0]
        assert app_row["is_latest_stage"] is False
        assert op_row["is_latest_stage"] is True

        # Approve final report -> flag moves again
        self.final_a.status = Dref.Status.APPROVED
        self.final_a.save(update_fields=["status"])
        resp_after_fr = self.client.get(f"/api/v2/dref3/{self.dref_a.appeal_code}/")
        self.assertEqual(resp_after_fr.status_code, status.HTTP_200_OK)
        data_after_fr = resp_after_fr.json()
        fr_row = [r for r in data_after_fr if r["stage"] == "Final Report"][0]
        op_row = [r for r in data_after_fr if r["stage"].startswith("Operational Update")][0]
        assert op_row["is_latest_stage"] is False
        assert fr_row["is_latest_stage"] is True
