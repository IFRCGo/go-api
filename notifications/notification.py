import os
import smtplib
from django.http import JsonResponse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


username = os.environ.get('EMAIL_USER')
password = os.environ.get('EMAIL_PASS')


def send_mail(recipients, msg):
    server = smtplib.SMTP('smtp.office365.com', '587')
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.sendmail(username, recipients, msg.as_string())
    server.quit()


def send_notification (recipients):
    if not username or not password:
        print('No EMAIL_USER and/or EMAIL_PASS set as environment variables')
        print('Cannot send notification')
        return

    msg = MIMEMultipart()

    msg['Subject'] = 'IFRC GO Notification'
    msg['From'] = username
    msg['To'] = ', '.join(recipients)

    body = MIMEText("""body""", 'html')
    msg.attach(body)

    try:
        send_mail(recipients, msg)
        print('Notifications sent!')
    except SMTPAuthenticationError:
        print('SMTPAuthenticationError')
        print('Cannot send notification')
