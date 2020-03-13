import os
import requests
import base64
# import threading
# import smtplib
from django.http import JsonResponse
from api.logger import logger
# from django.utils.html import strip_tags
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from api.models import CronJob, CronJobStatus


EMAIL_USER = os.environ.get('EMAIL_USER')
# EMAIL_PASS = os.environ.get('EMAIL_PASS')
# EMAIL_HOST = os.environ.get('EMAIL_HOST')
# EMAIL_PORT = os.environ.get('EMAIL_PORT')
IS_PROD = os.environ.get('PRODUCTION')
EMAIL_API_ENDPOINT = os.environ.get('EMAIL_API_ENDPOINT')
TEST_EMAILS = os.environ.get('TEST_EMAILS')


if TEST_EMAILS:
    TEST_EMAILS = TEST_EMAILS.split(',')
else:
    TEST_EMAILS = []
    TEST_EMAILS.append('gergely.horvath@ifrc.org')


def send_notification(subject, recipients, html, is_followed_event=False):
    # If it's not PROD only able to use test e-mail addresses which are set in the env var
    to_addresses = recipients
    if int(IS_PROD) != 1:
        logger.info('Using test email addresses...')
        to_addresses = []
        for eml in TEST_EMAILS:
            if eml and (eml in recipients):
                to_addresses.append(eml)

    recipients_as_string = ','.join(to_addresses)

    # Encode with base64 into bytes, then converting it back to strings for the JSON
    payload = {
        "FromAsBase64":str(base64.b64encode(EMAIL_USER.encode('utf-8')), 'utf-8'),
        "ToAsBase64":str(base64.b64encode('no-reply@ifrc.org'.encode('utf-8')), 'utf-8'),
        "CcAsBase64":"",
        "BccAsBase64":str(base64.b64encode(recipients_as_string.encode('utf-8')), 'utf-8'),
        "SubjectAsBase64":str(base64.b64encode(subject.encode('utf-8')), 'utf-8'),
        "BodyAsBase64":str(base64.b64encode(html.encode('utf-8')), 'utf-8'),
        "IsBodyHtml":True,
        "TemplateName":"",
        "TemplateLanguage":""
    }
    
    # The response contains the GUID (res.text) which could be used for future requests if something is wrong
    # TODO: It would be best to store the GUIDs and relevant mail parameters in some way, somewhere
    res = requests.post(EMAIL_API_ENDPOINT, json=payload)

    if res.status_code == 200:
        logger.info('E-mails were sent successfully.')
    elif res.status_code == 401:
        logger.info('Authorization failed to the e-mail sender API.')
    elif res.status_code == 500:
        logger.error('Could not reach the e-mail sender API.')

    return res.text


# # Old methods for sending email notifications (Leaving this here in case we ever need it for reference)
# class SendMail(threading.Thread):
#     def __init__(self, recipients, msg, **kwargs):
#         if int(IS_PROD) == 1:
#             self.recipients = recipients
#         else:
#             logger.info('Using test email addresses...')
#             self.recipients = []
#             for eml in TEST_EMAILS:
#                 if eml and (eml in recipients):
#                     self.recipients.append(eml)

#         self.msg = msg
#         super(SendMail, self).__init__(**kwargs)

#     def run(self):
#         try:
#             server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
#             server.ehlo()
#             server.starttls()
#             server.ehlo()
#             succ = server.login(EMAIL_USER, EMAIL_PASS)
#             if 'successful' not in str(succ[1]):
#                 body = { "name": "notification", "message": 'Error contacting ' + EMAIL_HOST + ' smtp server for notifications', "status": CronJobStatus.ERRONEOUS }
#                 CronJob.sync_cron(body)
#                 # ^ Mainly for index_and_notify.py cronjob log
#             if len(self.recipients) > 0:
#                 server.sendmail(EMAIL_USER, self.recipients, self.msg.as_string())
#             server.quit()
#             logger.info('Notifications sent!')
#         except smtplib.SMTPAuthenticationError:
#             logger.error('SMTPAuthenticationError')
#             logger.error('Cannot send notification')
#             logger.error(str(smtplib.SMTPAuthenticationError)[:100])


# def send_notification(subject, recipients, html):
#     if not username or not password:
#         logger.warn('No EMAIL_USER and/or EMAIL_PASS set as environment variables')
#         logger.warn('Cannot send notification')
#         return

#     msg = MIMEMultipart('alternative')

#     msg['Subject'] = '[IFRCGO] %s' % subject
#     msg['From'] = username.upper()
#     msg['To'] = 'no-reply@ifrc.org'

#     text_body = MIMEText(strip_tags(html), 'plain')
#     html_body = MIMEText(html, 'html')

#     msg.attach(text_body)
#     msg.attach(html_body)

#     SendMail(['no-reply@ifrc.org'] + recipients, msg).start()