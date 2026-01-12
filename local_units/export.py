from pathlib import Path
from typing import Callable
from django.conf import settings
from openpyxl import load_workbook

from django.http import HttpResponse

from local_units.bulk_upload import BASE_HEADER_MAP
from local_units.models import LocalUnit


def export_localunit(queryset, file_name=None):
    """
    Export LocalUnit data using the Administrative Bulk Import Template.
    """
    template_path = (
        Path(settings.BASE_DIR)
        / "go-static/files/local_units/Administrative Bulk Import Template - Local Units.xlsx"
    )
    if not file_name:
        file_name = "local_units_export.xlsx"

    wb = load_workbook(template_path)
    ws = wb.active

    # NOTE: Header is in row 2
    headers = [cell.value for cell in ws[2]]

    HEADER_VALUE_MAP: dict[str, Callable[[LocalUnit], any]] = {}

    for header, field_name in BASE_HEADER_MAP.items():
        if field_name == "date_of_data":
            HEADER_VALUE_MAP[header] = (
                lambda unit: unit.date_of_data.strftime("%Y-%m-%d")
                if unit.date_of_data
                else ""
            )
        elif field_name == "visibility":
            HEADER_VALUE_MAP[header] = (
                lambda unit: unit.get_visibility_display()
                if hasattr(unit, "get_visibility_display")
                else unit.visibility
            )
        elif field_name == "level":
            HEADER_VALUE_MAP[header] = (
                lambda unit: str(unit.level.name) if unit.level else ""
            )
        elif field_name in ["latitude", "longitude"]:
            HEADER_VALUE_MAP[header] = (
                lambda unit, f=field_name: unit.location.y
                if f == "latitude"
                else unit.location.x
                if unit.location
                else ""
            )
        else:
            HEADER_VALUE_MAP[header] = lambda unit, f=field_name: getattr(unit, f) or ""

    # NOTE: Data starts from row 4
    # TODO: USE SAME FROM BULK IMPORT?
    start_row = 4

    for row_idx, unit in enumerate(queryset, start=start_row):
        for col_idx, header in enumerate(headers, start=1):
            if header not in HEADER_VALUE_MAP:
                continue

            value = HEADER_VALUE_MAP[header](unit)
            ws.cell(row=row_idx, column=col_idx, value=value)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    wb.save(response)
    return response


def export_health_localunit(queryset, file_name=None):
    """
    Export LocalUnit data using the Health Bulk Import Template.
    """
    template_path = (
        Path(settings.BASE_DIR)
        / "go-static/files/local_units/Health Bulk Import Template - Local Units.xlsx"
    )
    if not file_name:
        file_name = "health_local_units_export.xlsx"
    pass
