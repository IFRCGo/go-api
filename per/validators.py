from typing import Any
from jsonschema import validate, ValidationError as JSONValidationError
from django.core.exceptions import ValidationError

from per.models import WorkPlanStatus


custom_component_schema = {
    "title": "Custom Component",
    "properties": {
        "actions": {
            "type": "string"
        },
        "due_date": {
            "type": "string",
            "format": "date"
        },
        "status": {
            "type": "number",
            "enum": [x.value for x in WorkPlanStatus]
        }
    },
    "required": ["actions", "due_date"],
}


def validate_custom_component(custom_component: dict):
    return validate_with_schema(custom_component_schema)(custom_component)


def validate_with_schema(schema: Any):
    def validator(data):
        try:
            validate(data, schema)
        except JSONValidationError as e:
            msg = e.message[:200] + "..." if len(e.message) > 200 else e.message
            raise ValidationError(f"Invalid data: {msg}")

    return validator
