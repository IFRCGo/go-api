from . import models

enum_register = {
    "deprecate_reason": models.LocalUnit.DeprecateReason,
    "validation_status": models.LocalUnitChangeRequest.Status,
    "validators": models.Validator,
    "local_unit_status": models.LocalUnit.Status,
}
