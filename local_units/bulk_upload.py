import csv
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, Generic, Literal, Type, TypeVar

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework.serializers import Serializer

from local_units.models import HealthData, LocalUnit, LocalUnitBulkUpload
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
        return ContentFile(self._output.getvalue())


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
            self.bulk_manager.add(LocalUnit(**serializer.validated_data, bulk_upload=self.bulk_upload))

    def run(self) -> None:
        with self.bulk_upload.file.open("r") as file:
            csv_reader = csv.DictReader(file)
            fieldnames = csv_reader.fieldnames or []

            context = self.get_context().__dict__
            error_writer = ErrorWriter(fieldnames)

            for row_index, row_data in enumerate(csv_reader, start=2):
                try:
                    data = {**row_data, **context}
                    self.process(data)
                    self.success_count += 1
                    error_writer.write(row_data, status=LocalUnitBulkUpload.Status.SUCCESS)
                except Exception as e:
                    self.failed_count += 1
                    error_writer.write(row_data, status=LocalUnitBulkUpload.Status.FAILED)
                    logger.warning(f"[BulkUpload:{self.bulk_upload.pk}] Row '{row_index}' failed: {e}")

        self.bulk_manager.done()
        self._finalize(error_writer)

    def _finalize(self, error_writer: ErrorWriter) -> None:
        if error_writer.has_errors():
            error_file = error_writer.to_content_file()
            self.bulk_upload.error_file.save("error_file.csv", error_file, save=False)

        self.bulk_upload.success_count = self.success_count
        self.bulk_upload.failed_count = self.failed_count
        self.bulk_upload.status = (
            LocalUnitBulkUpload.Status.SUCCESS if self.failed_count == 0 else LocalUnitBulkUpload.Status.FAILED
        )
        self.bulk_upload.save(
            update_fields=[
                "success_count",
                "failed_count",
                "status",
                "error_file",
            ]
        )

        logger.info(f"[BulkUpload:{self.bulk_upload.pk}] Completed: {self.success_count} success, {self.failed_count} failed.")


@dataclass
class LocalUnitUploadContext:
    country: int
    type: int
    created_by: int


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
        )

    def delete_existing_local_unit(self):
        with transaction.atomic():
            existing_local_units = LocalUnit.objects.filter(
                country_id=self.bulk_upload.country_id,
                type_id=self.bulk_upload.local_unit_type_id,
            )
            if existing_local_units.exists():
                count_existing_local_units = existing_local_units.count()
                existing_local_units.delete()
                logger.info(f"Deleted {count_existing_local_units} existing local units and continue with upload")
            logger.info("existing local units not found continue with bulk upload")

    def run(self) -> None:
        self.delete_existing_local_unit()
        return super().run()


class BulkUploadHealthData(BaseBulkUpload[LocalUnitUploadContext]):
    def __init__(self, bulk_upload: LocalUnitBulkUpload):
        from local_units.serializers import LocalUnitBulkUploadDetailSerializer

        self.serializer_class = LocalUnitBulkUploadDetailSerializer
        self.created_by = bulk_upload.triggered_by

        super().__init__(bulk_upload)

        self.health_field_names = get_model_field_names(
            HealthData,
        )

    def get_context(self) -> LocalUnitUploadContext:
        return LocalUnitUploadContext(
            country=self.bulk_upload.country_id,
            type=self.bulk_upload.local_unit_type_id,
            created_by=self.bulk_upload.triggered_by_id,
        )

    def delete_existing_local_unit(self):
        with transaction.atomic():
            existing_local_units = LocalUnit.objects.filter(
                country_id=self.bulk_upload.country_id,
                type_id=self.bulk_upload.local_unit_type_id,
            )
            if existing_local_units.exists():
                count_existing_local_units = existing_local_units.count()
                existing_local_units.delete()
                logger.info(f"Deleted {count_existing_local_units} existing local units and continue with upload")
            logger.info("existing local units not found continue with bulk upload")

    def process(self, data: dict[str, any]) -> None:
        health_data = {k: data.pop(k) for k in list(data.keys()) if k in self.health_field_names}
        if health_data:
            data["health"] = health_data

        serializer = self.serializer_class(
            data=data,
            context={
                "created_by_instance": self.bulk_upload.triggered_by,
                "created_by_pk": self.bulk_upload.triggered_by_id,
            },
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()

    def run(self) -> None:
        self.delete_existing_local_unit()
        return super().run()
