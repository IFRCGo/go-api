import os
import threading
import smtplib
from django.http import JsonResponse
from django.utils.html import strip_tags
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


username = os.environ.get('EMAIL_USER').upper()
password = os.environ.get('EMAIL_PASS')


class SendMail(threading.Thread):
    def __init__(self, recipients, msg, **kwargs):
        self.recipients = recipients
        self.msg = msg
        super(SendMail, self).__init__(**kwargs)

    def run(self):
        try:
            server = smtplib.SMTP('smtp.office365.com', '587')
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(username, self.recipients, self.msg.as_string())
            server.quit()
            print('Notifications sent!')
        except SMTPAuthenticationError:
            print('SMTPAuthenticationError')
            print('Cannot send notification')


def send_notification (recipients, html):
    if not username or not password:
        print('No EMAIL_USER and/or EMAIL_PASS set as environment variables')
        print('Cannot send notification')
        return

    msg = MIMEMultipart('alternative')

    msg['Subject'] = 'IFRC GO Notification'
    msg['From'] = username
    msg['To'] = ', '.join(recipients)

    text_body = MIMEText(strip_tags(html), 'plain')
    html_body = MIMEText(html, 'html')

    msg.attach(text_body)
    msg.attach(html_body)

    SendMail(recipients, msg).start()
