import base64
import logging

import requests
from django.conf import settings

from notifications.models import NotificationGUID
from notifications.notification import EMAIL_TO, clean_emails

logger = logging.getLogger(__name__)


def send_notification_dref(subject, recipients, html, mailtype="", cc_recipients=None):
    """DREF-specific notification sender: uses the DREF mailbox (EMAIL_API_ENDPOINT_DREF /
    EMAIL_USER_DREF), falling back to the shared email settings when those are unset.
    Unlike send_notification(), there is no SMTP fallback - a failed API call is just logged.
    """
    email_api_endpoint = settings.EMAIL_API_ENDPOINT_DREF or settings.EMAIL_API_ENDPOINT
    email_user = settings.EMAIL_USER_DREF or settings.EMAIL_USER

    cc_recipients = cc_recipients or []
    if not email_user or not email_api_endpoint:
        logger.warning("Cannot send DREF notifications.\nNo username and/or API endpoint set as environment variables.")
        if settings.DEBUG:
            print("-" * 22, "EMAIL START", "-" * 22)
            print(f"subject={subject}\nrecipients={recipients}\nhtml={html}\nmailtype={mailtype}")
            print("-" * 22, "EMAIL END -", "-" * 22)
        return

    recipients = recipients if isinstance(recipients, list) else [recipients]
    cc_recipients = cc_recipients if isinstance(cc_recipients, list) else [cc_recipients]

    to_addresses = clean_emails(recipients)
    cc_addresses = clean_emails(cc_recipients)
    addresses = to_addresses + cc_addresses

    if not addresses:
        logger.info("No valid email addresses provided for sending the DREF notification.")
        return

    if settings.DEBUG_EMAIL:
        print("-" * 22, "EMAIL START", "-" * 22)
        print(f"\n{html}\n")
        print("-" * 22, "EMAIL END -", "-" * 22)

    if "?" not in email_api_endpoint:  # a.k.a dirty disabling email sending
        return

    recipients_as_string = ",".join(to_addresses)
    cc_recipients_as_string = ",".join(cc_addresses)
    if not recipients_as_string:
        logger.info("Recipients string is empty")
        return  # If there are no recipients it's unnecessary to send out the email

    payload = {
        "FromAsBase64": str(base64.b64encode(email_user.encode("utf-8")), "utf-8"),
        "ToAsBase64": str(base64.b64encode(EMAIL_TO.encode("utf-8")), "utf-8"),
        "CcAsBase64": str(base64.b64encode(cc_recipients_as_string.encode("utf-8")), "utf-8"),
        "BccAsBase64": str(base64.b64encode(recipients_as_string.encode("utf-8")), "utf-8"),
        "SubjectAsBase64": str(base64.b64encode(subject.encode("utf-8")), "utf-8"),
        "BodyAsBase64": str(base64.b64encode(html.encode("utf-8")), "utf-8"),
        "IsBodyHtml": True,
        "TemplateName": "",
        "TemplateLanguage": "",
    }

    if len(to_addresses) == 1:
        payload["ToAsBase64"] = payload["BccAsBase64"]  # if 1 addressee, no BCC anonimization needed.
        payload["BccAsBase64"] = ""

    # The response contains the GUID (res.text)
    res = requests.post(email_api_endpoint, json=payload)
    res_text = res.text.replace('"', "")

    if res.status_code == 200:
        logger.info("Subject: {subject}, Recipients: {recs}".format(subject=subject, recs=recipients_as_string))
        logger.info("GUID: {}".format(res_text))
        # Saving GUID into a table so that the API can be queried with it to get info about
        # if the actual sending has failed or not.
        NotificationGUID.objects.create(
            api_guid=res_text,
            email_type=mailtype,
            to_list=f"To: {EMAIL_TO}; Cc: {cc_recipients_as_string}; Bcc: {recipients_as_string}",
        )
        logger.info("E-mails were sent successfully.")
    else:
        logger.error(
            f"DREF email send failed using API, status code: ({res.status_code})",
            extra={
                "content": res.content,
            },
        )
    return res.text
