from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions
from rest_framework.views import APIView


class AlertEmailPreview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_param = request.GET.get("type")
        param_type = {"alert"}
        if type_param not in param_type:
            return HttpResponse(f"Invalid 'type' parameter. Please use one of the following values: {', '.join(param_type)}.")

        context_mapping = {
            "alert": {
                "user_name": "Test User",
                "event_title": "Test Title",
                "event_description": "This is a test description for the alert email.",
                "start_datetime": "2025-11-28 01:00:00",
                "end_datetime": "2025-11-28 01:00:00",
                "country_name": [
                    "Nepal",
                ],
                "total_people_exposed": 1200,
                "total_buildings_exposed": 150,
                "hazard_types": "Flood",
                "related_montandon_events": [
                    {
                        "event_title": "Related Event 1",
                        "total_people_exposed": 100,
                        "total_buildings_exposed": 300,
                    },
                    {
                        "event_title": "Related Event 2",
                        "total_people_exposed": 200,
                        "total_buildings_exposed": 500,
                    },
                ],
                "related_go_events": [
                    "go-event-uuid-1",
                    "go-event-uuid-2",
                ],
            }
        }

        context = context_mapping.get(type_param)
        if context is None:
            return HttpResponse("No context found for the email preview.")

        template = loader.get_template("email/alert_system/alert.html")
        return HttpResponse(template.render(context, request))
