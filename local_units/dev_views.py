from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions
from rest_framework.views import APIView


class LocalUnitsEmailPreview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_param = request.GET.get("type")
        param_types = {"new", "update", "validate", "revert", "deprecate", "regional_validator", "global_validator"}

        if type_param not in param_types:
            return HttpResponse(f"Invalid type parameter. Please use one of the following values:  {', '.join(param_types)}.")

        context_mapping = {
            "new": {"new_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"},
            "update": {"update_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"},
            "validate": {"validate_success": True, "full_name": "Test User"},
            "revert": {"revert_reason": "Test Reason", "full_name": "Test User"},
            "deprecate": {"deprecate_local_unit": True, "deprecate_reason": "Test Deprecate Reason", "full_name": "Test User"},
            "regional_validator": {"is_validator_regional_admin": True, "full_name": "Regional User"},
            "global_validator": {"is_validator_global_admin": True, "full_name": "Global User"},
        }

        context = context_mapping.get(type_param)
        if context is None:
            return HttpResponse("No context found for the email preview.")

        template = loader.get_template("email/local_units/local_unit.html")
        return HttpResponse(template.render(context, request))
