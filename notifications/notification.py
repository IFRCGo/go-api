import base64
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from django.conf import settings
from django.utils.html import strip_tags

from api.logger import logger
from api.models import CronJob, CronJobStatus
from notifications.models import NotificationGUID

EMAIL_TO = "no-reply@ifrc.org"
IS_PROD = settings.GO_ENVIRONMENT == "production"


class SendMail(threading.Thread):
    def __init__(self, recipients, msg, **kwargs):
        self.recipients = recipients
        self.msg = msg
        super(SendMail, self).__init__(**kwargs)

    def run(self):
        try:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.ehlo()
            if settings.EMAIL_USE_TLS:
                server.starttls()
            server.ehlo()
            succ = server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            if "successful" not in str(succ[1]):
                cron_rec = {
                    "name": "notification",
                    "message": "Error contacting " + settings.EMAIL_HOST + " smtp server for notifications",
                    "status": CronJobStatus.ERRONEOUS,
                }
                CronJob.sync_cron(cron_rec)
            if len(self.recipients) > 0:
                server.sendmail(settings.EMAIL_USER, self.recipients, self.msg.as_string())
            server.quit()
            logger.info("E-mails were sent successfully.")
        except Exception as exc:
            logger.error("Could not send emails with Python smtlib", exc_info=True)
            ex = ""
            try:
                ex = str(exc.args)
            except Exception as exctwo:
                logger.warning(exctwo.args)
            cron_rec = {
                "name": "notification",
                "message": "Error sending out email with Python smtplib: {}".format(ex),
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(cron_rec)


def construct_msg(subject, html):
    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_USER.upper()
    msg["To"] = "no-reply@ifrc.org"

    text_body = MIMEText(strip_tags(html), "plain")
    html_body = MIMEText(html, "html")

    msg.attach(text_body)
    msg.attach(html_body)

    return msg


def send_notification(subject, recipients, html, mailtype="", files=None):
    """Generic email sending method, handly only HTML emails currently"""
    if not settings.EMAIL_USER or not settings.EMAIL_API_ENDPOINT:
        logger.warning("Cannot send notifications.\n" "No username and/or API endpoint set as environment variables.")
        if settings.DEBUG:
            print("-" * 22, "EMAIL START", "-" * 22)
            print(f"subject={subject}\nrecipients={recipients}\nhtml={html}\nmailtype={mailtype}")
            print("-" * 22, "EMAIL END -", "-" * 22)
        return
    if settings.DEBUG_EMAIL:
        print("-" * 22, "EMAIL START", "-" * 22)
        print(f"\n{html}\n")
        print("-" * 22, "EMAIL END -", "-" * 22)

    if settings.FORCE_USE_SMTP:
        logger.info("Forcing SMPT usage for sending emails.")
        msg = construct_msg(subject, html)
        SendMail(recipients, msg).start()
        return

    if "?" not in settings.EMAIL_API_ENDPOINT:  # a.k.a dirty disabling email sending
        return

    to_addresses = recipients if isinstance(recipients, list) else [recipients]

    #    if not IS_PROD:
    #        logger.info('Using test email addresses...')
    #        to_addresses = []
    #        logger.info(to_addresses)
    #        for eml in settings.TEST_EMAILS:
    #
    #            # It is possible to filter test addressees to domain name only – not used.
    #            is_dom = True if '@' not in eml else False
    #            if is_dom:
    #                for rec in recipients:
    #                    try:
    #                        if eml == rec.split('@')[1]:
    #                            to_addresses.append(rec)
    #                    except Exception:
    #                        logger.info('Could not extract domain from: {}'.format(rec))
    #            elif eml and (eml in recipients):
    #                to_addresses.append(eml)

    recipients_as_string = ",".join(to_addresses)
    if not recipients_as_string:
        if len(to_addresses) > 0:
            warn_msg = "Recipients failed to be converted to string, 1st rec.: {}".format(to_addresses[0])
            logger.info(warn_msg)
            # Save the warning into the CronJob logs too
            cron_error = {"name": "index_and_notify", "message": warn_msg, "status": CronJobStatus.WARNED}
            CronJob.sync_cron(cron_error)
        else:
            logger.info("Recipients string is empty")
        return  # If there are no recipients it's unnecessary to send out the email

    # Encode with base64 into bytes, then converting it back to strings for the JSON
    payload = {
        "FromAsBase64": str(base64.b64encode(settings.EMAIL_USER.encode("utf-8")), "utf-8"),
        "ToAsBase64": str(base64.b64encode(EMAIL_TO.encode("utf-8")), "utf-8"),
        "CcAsBase64": "",
        "BccAsBase64": str(base64.b64encode(recipients_as_string.encode("utf-8")), "utf-8"),
        "SubjectAsBase64": str(base64.b64encode(subject.encode("utf-8")), "utf-8"),
        "BodyAsBase64": str(base64.b64encode(html.encode("utf-8")), "utf-8"),
        "IsBodyHtml": True,
        "TemplateName": "",
        "TemplateLanguage": "",
    }

    # The response contains the GUID (res.text)
    res = requests.post(settings.EMAIL_API_ENDPOINT, json=payload)
    res_text = res.text.replace('"', "")

    if res.status_code == 200:
        logger.info("Subject: {subject}, Recipients: {recs}".format(subject=subject, recs=recipients_as_string))

        logger.info("GUID: {}".format(res_text))
        # Saving GUID into a table so that the API can be queried with it to get info about
        # if the actual sending has failed or not.
        NotificationGUID.objects.create(
            api_guid=res_text, email_type=mailtype, to_list=f"To: {EMAIL_TO}; Bcc: {recipients_as_string}"
        )

        logger.info("E-mails were sent successfully.")
    else:
        logger.error(
            f"Email send failed using API, status code: ({res.status_code})",
            extra={
                "content": res.content,
            },
        )
        # Try sending with Python smtplib, if reaching the API fails
        logger.warning(f"Authorization/authentication failed ({res.status_code}) to the e-mail sender API.")
        msg = construct_msg(subject, html)
        SendMail(to_addresses, msg).start()
    return res.text
