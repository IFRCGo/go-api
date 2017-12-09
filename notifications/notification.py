import os
import smtplib
from django.http import JsonResponse
from django.utils.html import strip_tags
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


username = os.environ.get('EMAIL_USER').upper()
password = os.environ.get('EMAIL_PASS')


def send_mail(recipients, msg):
    server = smtplib.SMTP('smtp.office365.com', '587')
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.sendmail(username, recipients, msg.as_string())
    server.quit()


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

    try:
        send_mail(recipients, msg)
        print('Notifications sent!')
    except SMTPAuthenticationError:
        print('SMTPAuthenticationError')
        print('Cannot send notification')
