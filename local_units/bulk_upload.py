import csv
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, Generic, Literal, Optional, Type, TypeVar

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework.serializers import Serializer

from local_units.models import HealthData, LocalUnit, LocalUnitBulkUpload, LocalUnitType
from local_units.utils import get_model_field_names
from main.managers import BulkCreateManager

logger = logging.getLogger(__name__)


ContextType = TypeVar("ContextType")


class BulkUploadError(Exception):
    """Custom exception for bulk upload errors."""

    pass


class ErrorWriter:
    def __init__(self, fieldnames: list[str]):
        self._fieldnames = ["upload_status"] + fieldnames
        self._output = io.StringIO()
        self._writer = csv.DictWriter(self._output, fieldnames=self._fieldnames)
        self._writer.writeheader()
        self._has_errors = False

    def write(
        self, row: dict[str, str], status: Literal[LocalUnitBulkUpload.Status.SUCCESS, LocalUnitBulkUpload.Status.FAILED]
    ) -> None:
        self._writer.writerow({"upload_status": status.name, **row})
        if status == LocalUnitBulkUpload.Status.FAILED:
            self._has_errors = True

    def has_errors(self) -> bool:
        return self._has_errors

    def to_content_file(self) -> ContentFile:
        return ContentFile(self._output.getvalue().encode("utf-8"))


class BaseBulkUpload(Generic[ContextType]):
    serializer_class: Type[Serializer]

    def __init__(self, bulk_upload: LocalUnitBulkUpload):
        if self.serializer_class is None:
            raise ValueError("serializer_class must be defined in the subclass.")

        self.bulk_upload = bulk_upload
        self.success_count: int = 0
        self.failed_count: int = 0
        self.bulk_manager: BulkCreateManager = BulkCreateManager(chunk_size=500)
        self.error_writer: Optional[ErrorWriter] = None

    def get_context(self) -> ContextType:
        raise NotImplementedError("Subclasses must implement get_context method.")

    def delete_existing_local_unit(self):
        """Delete existing local units based on the context."""
        pass

    def _validate_csv(self, fieldnames) -> None:
        pass

    def process_row(self, data: Dict[str, Any]) -> bool:
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            self.bulk_manager.add(LocalUnit(**serializer.validated_data))
            return True
        return False

    def run(self) -> None:
        with self.bulk_upload.file.open("r") as file:
            csv_reader = csv.DictReader(file)
            fieldnames = csv_reader.fieldnames or []

            try:
                self._validate_csv(fieldnames)
            except ValueError as e:
                self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
                self.bulk_upload.error_message = str(e)
                self.bulk_upload.save(update_fields=["status", "error_message"])
                logger.error(f"[BulkUpload:{self.bulk_upload.pk}] Validation error: {str(e)}")
                return

            context = self.get_context().__dict__
            self.error_writer = ErrorWriter(fieldnames)
            try:
                with transaction.atomic():
                    self.delete_existing_local_unit()
                    for row_index, row_data in enumerate(csv_reader, start=2):
                        data = {**row_data, **context}
                        if self.process_row(data):
                            self.success_count += 1
                            self.error_writer.write(row_data, status=LocalUnitBulkUpload.Status.SUCCESS)
                        else:
                            self.failed_count += 1
                            self.error_writer.write(row_data, status=LocalUnitBulkUpload.Status.FAILED)
                            logger.warning(f"[BulkUpload:{self.bulk_upload.pk}] Row '{row_index}' failed")

                    if self.failed_count > 0:
                        raise BulkUploadError("Bulk upload failed with some errors.")

                    self.bulk_manager.done()
                    self._finalize_success()
            except BulkUploadError:
                self._finalize_failure()

    def _finalize_success(self) -> None:
        self.bulk_upload.success_count = self.success_count
        self.bulk_upload.failed_count = 0
        self.bulk_upload.status = LocalUnitBulkUpload.Status.SUCCESS
        self.bulk_upload.save(update_fields=["success_count", "failed_count", "status"])

        logger.info(f"[BulkUpload:{self.bulk_upload.pk}] SUCCESS: {self.success_count} rows.")

    def _finalize_failure(self) -> None:
        if self.error_writer and self.error_writer.has_errors():
            error_file = self.error_writer.to_content_file()
            self.bulk_upload.error_file.save("error_file.csv", error_file, save=True)

        self.bulk_upload.success_count = 0
        self.bulk_upload.failed_count = self.failed_count
        self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
        self.bulk_upload.save(update_fields=["success_count", "failed_count", "status", "error_file"])

        logger.info(
            f"[BulkUpload:{self.bulk_upload.pk}] FAILED: "
            f"{self.bulk_upload.success_count} succeeded, {self.failed_count} failed."
        )


@dataclass(frozen=True)
class LocalUnitUploadContext:
    country: int
    type: int
    created_by: int
    bulk_upload: int


class BaseBulkUploadLocalUnit(BaseBulkUpload[LocalUnitUploadContext]):

    def __init__(self, bulk_upload: LocalUnitBulkUpload):
        from local_units.serializers import LocalUnitBulkUploadDetailSerializer

        self.serializer_class = LocalUnitBulkUploadDetailSerializer
        super().__init__(bulk_upload)

    def get_context(self) -> LocalUnitUploadContext:
        return LocalUnitUploadContext(
            country=self.bulk_upload.country_id,
            type=self.bulk_upload.local_unit_type_id,
            created_by=self.bulk_upload.triggered_by_id,
            bulk_upload=self.bulk_upload.pk,
        )

    def delete_existing_local_unit(self):
        queryset = LocalUnit.objects.filter(
            country_id=self.bulk_upload.country_id,
            type_id=self.bulk_upload.local_unit_type_id,
        )
        if queryset.exists():
            count, _ = queryset.delete()
            logger.info(f"Deleted {count} existing local units before upload.")
        else:
            logger.info("No existing local units found for deletion.")

    def _validate_csv(self, fieldnames) -> None:
        health_field_names = set(get_model_field_names(HealthData))
        present_health_fields = health_field_names & set(fieldnames)

        local_unit_type = LocalUnitType.objects.filter(id=self.bulk_upload.local_unit_type_id).first()
        if not local_unit_type:
            raise ValueError("Invalid local unit type")

        if present_health_fields and local_unit_type.name.strip().lower() != "health care":
            raise ValueError(f"Health data are not allowed for this type: {local_unit_type.name}.")


class BulkUploadHealthData(BaseBulkUpload[LocalUnitUploadContext]):
    def __init__(self, bulk_upload: LocalUnitBulkUpload):
        from local_units.serializers import LocalUnitBulkUploadDetailSerializer

        self.serializer_class = LocalUnitBulkUploadDetailSerializer
        super().__init__(bulk_upload)

        self.health_field_names = get_model_field_names(
            HealthData,
        )

    def get_context(self) -> LocalUnitUploadContext:
        return LocalUnitUploadContext(
            country=self.bulk_upload.country_id,
            type=self.bulk_upload.local_unit_type_id,
            created_by=self.bulk_upload.triggered_by_id,
            bulk_upload=self.bulk_upload.pk,
        )

    def delete_existing_local_unit(self):
        local_unit_queryset = LocalUnit.objects.filter(
            country_id=self.bulk_upload.country_id,
            type_id=self.bulk_upload.local_unit_type_id,
        )
        if local_unit_queryset.exists():
            health_data_ids = local_unit_queryset.filter(health__isnull=False).values_list("health__id", flat=True)
            health_data_count, _ = HealthData.objects.filter(id__in=health_data_ids).delete()
            count, _ = local_unit_queryset.delete()
            logger.info(f"Deleted {count} existing local units and {health_data_count} health data before upload.")
        else:
            logger.info("No existing local units found for deletion.")

    def process_row(self, data: dict[str, any]) -> bool:
        health_data = {k: data.get(k) for k in list(data.keys()) if k in self.health_field_names}
        if health_data:
            data["health"] = health_data
        return super().process_row(data)
