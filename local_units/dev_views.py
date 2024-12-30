from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions
from rest_framework.views import APIView


class LocalUnitsEmailPreview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_param = request.GET.get("type")
        param_types = {"new", "update", "validate", "revert", "deprecate", "regional", "global"}

        if type_param not in param_types:
            return HttpResponse(f"Invalid type parameter. Please use one of the following values:  {', '.join(param_types)}.")

        if type == "new":
            context = {"new_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"}
        elif type == "update":
            context = {"update_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"}
        elif type == "validate":
            context = {"validate_success": True, "full_name": "Test User"}
        elif type == "revert":
            context = {"revert_reason": "Test Reason", "full_name": "Test User"}
        elif type == "deprecate":
            context = {"deprecate_local_unit": True, "deprecate_reason": "Test Deprecate Reason", "full_name": "Test User"}
        elif type == "regional":
            context = {"regional_admin": True, "full_name": "Regional User"}
        elif type == "global":
            context = {"global_admin": True, "full_name": "Global User"}
        else:
            return HttpResponse("No context found for the email preview..")

        template = loader.get_template("email/local_units/local_unit.html")
        return HttpResponse(template.render(context, request))
