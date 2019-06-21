import os
import threading
import smtplib
from django.http import JsonResponse
from django.utils.html import strip_tags
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from api.logger import logger


username = os.environ.get('EMAIL_USER')
password = os.environ.get('EMAIL_PASS')
emailhost = os.environ.get('EMAIL_HOST')
emailport = os.environ.get('EMAIL_PORT')
prod = os.environ.get('PRODUCTION')

testEmails=os.environ.get('TEST_EMAILS')
if testEmails:
    testEmails = testEmails.split(',')
else:
    testEmails=[]
    testEmails.append('zoltan.szabo@ifrc.org')


class SendMail(threading.Thread):
    def __init__(self, recipients, msg, **kwargs):

        if int(prod) == 1:
            self.recipients = recipients
        else:
            logger.info('Using test email addresses...')
            self.recipients = []
            for eml in testEmails:
                if eml and (eml in recipients):
                    self.recipients.append(eml)

        self.msg = msg
        super(SendMail, self).__init__(**kwargs)

    def run(self):
        try:
            server = smtplib.SMTP(emailhost, emailport)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            if len(self.recipients) > 0:
                server.sendmail(username, self.recipients, self.msg.as_string())
            server.quit()
            logger.info('Notifications sent!')
        except SMTPAuthenticationError:
            logger.error('SMTPAuthenticationError')
            logger.error('Cannot send notification')
            logger.error(str(SMTPAuthenticationError)[:100])


def send_notification (subject, recipients, html):
    if not username or not password:
        logger.warn('No EMAIL_USER and/or EMAIL_PASS set as environment variables')
        logger.warn('Cannot send notification')
        return

    msg = MIMEMultipart('alternative')

    msg['Subject'] = '[IFRCGO] %s' % subject
    msg['From'] = username.upper()
    msg['To'] = 'no-reply@ifrc.org'

    text_body = MIMEText(strip_tags(html), 'plain')
    html_body = MIMEText(html, 'html')

    msg.attach(text_body)
    msg.attach(html_body)

    SendMail(['no-reply@ifrc.org'] + recipients, msg).start()
