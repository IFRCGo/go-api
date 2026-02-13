from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions
from rest_framework.views import APIView


class EAPEmailPreview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_param = request.GET.get("type")

        template_map = {
            "registration": "email/eap/registration.html",
            "submission": "email/eap/submission.html",
            "feedback_to_national_society": "email/eap/feedback_to_national_society.html",
            "resubmission_of_revised_eap": "email/eap/re-submission.html",
            "feedback_for_revised_eap": "email/eap/feedback_to_revised_eap.html",
            "technically_validated_eap": "email/eap/technically_validated_eap.html",
            "pending_pfa": "email/eap/pending_pfa.html",
            "approved_eap": "email/eap/approved.html",
            "reminder": "email/eap/reminder.html",
            "share_eap": "email/eap/share_eap.html",
        }

        if type_param not in template_map:
            valid_values = ", ".join(template_map.keys())
            return HttpResponse(
                f"Invalid 'type' parameter. Please use one of the following values: {valid_values}.",
            )

        context_map = {
            "registration": {
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "supporting_partners": [
                    {"society_name": "Partner 1"},
                    {"society_name": "Partner 2"},
                ],
                "disaster_type": "Flood",
                "ns_contact_name": "Test registration name",
                "ns_contact_email": "test.registration@example.com",
                "ns_contact_phone": "1234567890",
            },
            "submission": {
                "eap_type_display": "SIMPLIFIED EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "people_targated": 100,
                "latest_eap_id": 1,
                "supporting_partners": [
                    {"society_name": "Partner NS 1"},
                    {"society_name": "Partner NS 2"},
                ],
                "disaster_type": "Flood",
                "total_budget": "250,000 CHF",
                "ns_contact_name": "Test Ns Contact name",
                "ns_contact_email": "test.Ns@gmail.com",
                "ns_contact_phone": "+977-9800000000",
            },
            "feedback_to_national_society": {
                "registration_id": 1,
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
            },
            "resubmission_of_revised_eap": {
                "latest_eap_id": 1,
                "eap_type_display": "SIMPLIFIED EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "supporting_partners": [
                    {"society_name": "Partner NS 1"},
                    {"society_name": "Partner NS 2"},
                ],
                "version": 2 or 3,
                "people_targated": 100,
                "disaster_type": "Flood",
                "total_budget": "250,000 CHF",
                "ns_contact_name": "Test Ns Contact name",
                "ns_contact_email": "test.Ns@gmail.com",
                "ns_contact_phone": "+977-9800000000",
            },
            "feedback_for_revised_eap": {
                "registration_id": 1,
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "version": 2,
            },
            "technically_validated_eap": {
                "registration_id": 1,
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "disaster_type": "Flood",
            },
            "pending_pfa": {
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "disaster_type": "Flood",
            },
            "approved_eap": {
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "disaster_type": "Flood",
            },
            "reminder": {
                "eap_type_display": "FULL EAP",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "disaster_type": "Flood",
            },
            "share_eap": {
                "registration_id": 1,
                "eap_type": "simplified",
                "country_name": "Test Country",
                "national_society": "Test National Society",
                "disaster_type": "Flood",
            },
        }

        context = context_map.get(type_param)
        if context is None:
            return HttpResponse("No context found for the email preview.")
        template_file = template_map[type_param]
        template = loader.get_template(template_file)
        return HttpResponse(template.render(context, request))
