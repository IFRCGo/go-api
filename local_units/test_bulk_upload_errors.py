import unittest
from types import SimpleNamespace

from rest_framework.exceptions import ErrorDetail

from local_units.bulk_upload import ErrorWriter


class ErrorWriterTests(unittest.TestCase):
    HEADER_MAP = {
        "Local Unit Name (En)": "english_branch_name",
        "Latitude": "latitude",
        "Longitude": "longitude",
    }

    def _writer(self):
        return ErrorWriter(
            fieldnames=["Local Unit Name (En)", "Latitude", "Longitude"],
            header_map=self.HEADER_MAP,
        )

    def test_maps_serializer_field_to_display_header(self):
        writer = self._writer()
        formatted = writer._format_errors({"latitude": ["This field is required."]})
        self.assertIn("Latitude", formatted)
        self.assertEqual(formatted["Latitude"], ["This field is required."])

    def test_maps_non_field_errors_to_general_error_column(self):
        writer = self._writer()
        formatted = writer._format_errors({"non_field_errors": ["Branch Name Combination is required."]})
        self.assertIn("General Error", formatted)
        self.assertNotIn("non_field_errors", formatted)

    def test_maps_location_error_to_latitude_and_longitude(self):
        writer = self._writer()
        formatted = writer._format_errors({"location": ["Input coordinates is outside country boundary"]})
        self.assertEqual(formatted["Latitude"], ["Input coordinates is outside country boundary"])
        self.assertEqual(formatted["Longitude"], ["Input coordinates is outside country boundary"])

    def test_write_failed_row_includes_error_columns(self):
        writer = self._writer()
        writer.write(
            {"english_branch_name": "Test", "latitude": "", "longitude": ""},
            status=SimpleNamespace(name="FAILED"),
            error_detail={
                "latitude": [ErrorDetail("Latitude and Longitude are required.", code="invalid")],
                "longitude": [ErrorDetail("Latitude and Longitude are required.", code="invalid")],
            },
        )
        headers = [writer._ws.cell(row=1, column=i).value for i in range(1, writer._ws.max_column + 1)]
        self.assertIn("Latitude_error", headers)
        self.assertIn("Longitude_error", headers)
        self.assertEqual(writer._ws.cell(row=2, column=headers.index("Latitude_error") + 1).value, "Latitude and Longitude are required.")


if __name__ == "__main__":
    unittest.main()
