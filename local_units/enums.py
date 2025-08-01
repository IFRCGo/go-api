from . import models

enum_register = {
    "deprecate_reason": models.LocalUnit.DeprecateReason,
    "validation_status": models.LocalUnitChangeRequest.Status,
    "validators": models.Validator,
    "bulk_upload_status": models.LocalUnitBulkUpload.Status,
}
