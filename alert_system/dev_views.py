from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions
from rest_framework.views import APIView


class AlertEmailPreview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_param = request.GET.get("type")

        template_map = {
            "alert": "email/alert_system/alert_notification.html",
            "alert_reply": "email/alert_system/alert_notification_reply.html",
        }

        if type_param not in template_map:
            valid_values = ", ".join(template_map.keys())
            return HttpResponse(
                f"Invalid 'type' parameter. Please use one of the following values: {valid_values}.",
            )
        context_map = {
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
                        "start_datetime": "2025-11-28 01:00:00",
                        "end_datetime": "2025-11-28 01:00:00",
                    },
                    {
                        "event_title": "Related Event 2",
                        "total_people_exposed": 200,
                        "total_buildings_exposed": 500,
                        "start_datetime": "2025-11-28 01:00:00",
                        "end_datetime": "2025-11-28 01:00:00",
                    },
                ],
                "related_go_events": [
                    "go-event-uuid-1",
                    "go-event-uuid-2",
                ],
            },
            "alert_reply": {
                "event_title": "Test Title",
                "event_description": "This is a test description for the alert email.",
                "start_datetime": "2025-11-28 01:00:00",
                "end_datetime": "2025-11-28 01:00:00",
                "country_name": [
                    "Nepal",
                ],
                "total_people_exposed": 1200,
                "total_buildings_exposed": 150,
            },
        }

        context = context_map.get(type_param)
        if context is None:
            return HttpResponse("No context found for the email preview.")
        template_file = template_map[type_param]
        template = loader.get_template(template_file)
        return HttpResponse(template.render(context, request))
