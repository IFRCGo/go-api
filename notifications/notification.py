import os
import requests
import base64
from api.logger import logger
from api.models import CronJob, CronJobStatus
from notifications.models import NotificationGUID

# EMAIL_PASS = os.environ.get('EMAIL_PASS')
# EMAIL_HOST = os.environ.get('EMAIL_HOST')
# EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_API_ENDPOINT = os.environ.get('EMAIL_API_ENDPOINT')
EMAIL_TO = 'no-reply@ifrc.org'
IS_PROD = os.environ.get('PRODUCTION')

test_emails = os.environ.get('TEST_EMAILS')
if test_emails:
    test_emails = test_emails.split(',')
else:
    test_emails = ['gergely.horvath@ifrc.org']


def send_notification(subject, recipients, html, mailtype=''):
    """ Generic email sending method, handly only HTML emails currently """
    if not EMAIL_USER or not EMAIL_API_ENDPOINT:
        logger.warn('Cannot send notifications.')
        logger.warn('No username and/or API endpoint set as environment variables.')
        return

    # If it's not PROD only able to use test e-mail addresses which are set in the env var
    to_addresses = recipients
    if int(IS_PROD) != 1:
        logger.info('Using test email addresses...')
        to_addresses = []
        for eml in test_emails:
            is_dom = True if '@' not in eml else False
            if is_dom:
                for rec in recipients:
                    if eml == rec.split('@')[1]:
                        to_addresses.append(rec)
            elif eml and (eml in recipients):
                to_addresses.append(eml)

    recipients_as_string = ','.join(to_addresses)
    if not recipients_as_string:
        if len(to_addresses) > 0:
            warn_msg = 'Recipients failed to be converted to string, 1st rec.: {}'.format(to_addresses[0])
            logger.info(warn_msg)
            # Save the warning into the CronJob logs too
            cron_error = {"name": "index_and_notify", "message": warn_msg, "status": CronJobStatus.WARNED}
            CronJob.sync_cron(cron_error)
        else:
            logger.info('Recipients string is empty')
        return  # If there are no recipients it's unnecessary to send out the email

    # Encode with base64 into bytes, then converting it back to strings for the JSON
    payload = {
        "FromAsBase64": str(base64.b64encode(EMAIL_USER.encode('utf-8')), 'utf-8'),
        "ToAsBase64": str(base64.b64encode(EMAIL_TO.encode('utf-8')), 'utf-8'),
        "CcAsBase64": "",
        "BccAsBase64": str(base64.b64encode(recipients_as_string.encode('utf-8')), 'utf-8'),
        "SubjectAsBase64": str(base64.b64encode(subject.encode('utf-8')), 'utf-8'),
        "BodyAsBase64": str(base64.b64encode(html.encode('utf-8')), 'utf-8'),
        "IsBodyHtml": True,
        "TemplateName": "",
        "TemplateLanguage": ""
    }

    # The response contains the GUID (res.text)
    res = requests.post(EMAIL_API_ENDPOINT, json=payload)
    res_text = res.text.replace('"', '')

    if res.status_code == 200:
        logger.info('Subject: {subject}, Recipients: {recs}'.format(subject=subject, recs=recipients_as_string))

        logger.info('GUID: {}'.format(res_text))
        # Saving GUID into a table so that the API can be queried with it to get info about
        # if the actual sending has failed or not.
        NotificationGUID.objects.create(
            api_guid=res_text,
            email_type=mailtype,
            to_list='To: {to}; Bcc: {bcc}'.format(to=EMAIL_TO, bcc=recipients_as_string)
        )

        logger.info('E-mails were sent successfully.')
    elif res.status_code == 401 or res.status_code == 403:
        logger.error('Authorization/authentication failed ({}) to the e-mail sender API.'.format(res.status_code))
    elif res.status_code == 500:
        logger.error('Could not reach the e-mail sender API.')
    else:
        logger.info(res_text)

    return res.text
