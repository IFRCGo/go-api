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

    def get_context(self) -> ContextType:
        raise NotImplementedError("Subclasses must implement get_context method.")

    def process(self, data: Dict[str, Any]) -> None:
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            self.bulk_manager.add(LocalUnit(**serializer.validated_data))

    @transaction.atomic
    def run(self) -> None:
        error_writer: Optional[ErrorWriter] = None
        with self.bulk_upload.file.open("r") as file:
            csv_reader = csv.DictReader(file)
            fieldnames = csv_reader.fieldnames or []
            context = self.get_context().__dict__
            error_writer = ErrorWriter(fieldnames)

            for row_index, row_data in enumerate(csv_reader, start=2):
                data = {**row_data, **context}
                try:
                    self.process(data)
                    self.success_count += 1
                    error_writer.write(row_data, status=LocalUnitBulkUpload.Status.SUCCESS)
                except Exception as e:
                    self.failed_count += 1
                    error_writer.write(row_data, status=LocalUnitBulkUpload.Status.FAILED)
                    logger.warning(f"[BulkUpload:{self.bulk_upload.pk}] Row '{row_index}' failed: {e}")
                    raise

            if self.failed_count > 0:
                self._finalize_failure(error_writer)
                return
            self.bulk_manager.done()
            self._finalize_success()

    def _finalize_success(self) -> None:
        self.bulk_upload.success_count = self.success_count
        self.bulk_upload.failed_count = 0
        self.bulk_upload.status = LocalUnitBulkUpload.Status.SUCCESS
        self.bulk_upload.save(update_fields=["success_count", "failed_count", "status"])

        logger.info(f"[BulkUpload:{self.bulk_upload.pk}] SUCCESS: {self.success_count} rows.")

    def _finalize_failure(self, error_writer: Optional[ErrorWriter]) -> None:
        if error_writer and error_writer.has_errors():
            error_file = error_writer.to_content_file()
            self.bulk_upload.error_file.save("error_file.csv", error_file, save=True)

        self.bulk_upload.success_count = 0
        self.bulk_upload.failed_count = self.failed_count
        self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
        self.bulk_upload.save(update_fields=["success_count", "failed_count", "status", "error_file"])

        logger.info(
            f"[BulkUpload:{self.bulk_upload.pk}] FAILED: "
            f"{self.bulk_upload.success_count} succeeded, {self.failed_count} failed."
        )


@dataclass
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
        existing = LocalUnit.objects.filter(
            country_id=self.bulk_upload.country_id,
            type_id=self.bulk_upload.local_unit_type_id,
        )
        if existing.exists():
            count = existing.count()
            existing.delete()
            logger.info(f"Deleted {count} existing local units before upload.")
        else:
            logger.info("No existing local units found for deletion.")

    def validate_csv(self, file) -> None:
        file.seek(0)
        csv_reader = csv.DictReader(file)
        csv_columns = set(csv_reader.fieldnames or [])
        health_field_names = set(get_model_field_names(HealthData))
        present_health_fields = health_field_names.intersection(csv_columns)

        local_unit_type = LocalUnitType.objects.filter(id=self.bulk_upload.local_unit_type_id).first()
        if not local_unit_type:
            raise ValueError("Invalid local unit type")

        if present_health_fields and local_unit_type.name.strip().lower() != "health care":
            raise ValueError(f"Health data are not allowed for this type: {local_unit_type.name}.")

    @transaction.atomic
    def run(self) -> None:
        try:
            with self.bulk_upload.file.open("r") as file:
                self.validate_csv(file)
        except ValueError as e:
            self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
            self.bulk_upload.error_message = str(e)
            self.bulk_upload.save(update_fields=["status", "error_message"])
            return
        try:
            self.delete_existing_local_unit()
            super().run()
        except Exception:
            self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
            self.bulk_upload.save(update_fields=["status"])
            raise


class BulkUploadHealthData(BaseBulkUpload[LocalUnitUploadContext]):
    def __init__(self, bulk_upload: LocalUnitBulkUpload):
        from local_units.serializers import LocalUnitBulkUploadDetailSerializer

        self.serializer_class = LocalUnitBulkUploadDetailSerializer
        super().__init__(bulk_upload)

        self.health_field_names = get_model_field_names(
            HealthData,
        )
        self.context = {
            "type": bulk_upload.local_unit_type,
            "created_by": bulk_upload.triggered_by,
        }

    def get_context(self) -> LocalUnitUploadContext:
        return LocalUnitUploadContext(
            country=self.bulk_upload.country_id,
            type=self.bulk_upload.local_unit_type_id,
            created_by=self.bulk_upload.triggered_by_id,
            bulk_upload=self.bulk_upload.pk,
        )

    def delete_existing_local_unit(self):
        existing = LocalUnit.objects.filter(
            country_id=self.bulk_upload.country_id,
            type_id=self.bulk_upload.local_unit_type_id,
        )
        if existing.exists():
            count = existing.count()
            existing.delete()
            logger.info(f"Deleted {count} existing local units before upload.")
        else:
            logger.info("No existing local units found for deletion.")

    def process(self, data: dict[str, any]) -> None:
        upload_context = self.get_context()
        data.update(
            {
                "country": upload_context.country,
                "type": upload_context.type,
                "created_by": upload_context.created_by,
                "bulk_upload": self.bulk_upload.id,
            }
        )
        health_data = {k: data.pop(k) for k in list(data.keys()) if k in self.health_field_names}
        if health_data:
            data["health"] = health_data
            super().process(data)

    @transaction.atomic
    def run(self) -> None:
        try:
            super().run()
        except Exception:
            self.bulk_upload.status = LocalUnitBulkUpload.Status.FAILED
            self.bulk_upload.save(update_fields=["status"])
            raise
