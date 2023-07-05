from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.conf import settings
from django.template.loader import render_to_string

from api.models import Country, Profile, UserRegion
from .models import DomainWhitelist
from notifications.notification import send_notification


def create_inactive_user(
    username,
    first_name,
    last_name,
    email,
    password
):
    user = User.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_active=False
    )
    return user


def set_user_profile(
    user,
    country,
    organization_type,
    organization,
    city,
    department,
    position,
    phone_number
):
    user.profile.country = Country.objects.get(pk=country)
    user.profile.org_type = organization_type
    user.profile.org = organization
    user.profile.city = city
    user.profile.department = department
    user.profile.position = position
    user.profile.phone_number = phone_number
    user.save()
    return user


def is_valid_domain(email):
    domain = email.lower().split('@')[1]
    is_allowed = (
        DomainWhitelist.objects.filter(
            is_active=True
        ).annotate(
            domain_name_lower=Lower('domain_name')
        ).filter(
            domain_name_lower=domain
        ).exists()
    )

    if is_allowed or domain in ['ifrc.org', 'arcs.org.af', 'voroskereszt.hu']:
        return True
    return False


def get_valid_admins(contacts):
    if not type(contacts) is list:
        return False
    # Get the emails into an array, don't include None
    emails = [admin.get('email', None) for admin in contacts if admin.get('email', None)]
    # Currently we enforce 2 admins to validate
    if len(emails) < 2:
        return False
    is_admin1 = User.objects.filter(email__iexact=emails[0]).exists()
    is_admin2 = User.objects.filter(email__iexact=emails[1]).exists()
    if is_admin1 is False or is_admin2 is False:
        return False
    return emails


def getRegionalAdmins(userId):
    countryId = Profile.objects.get(user_id=userId).country_id
    regionId = Country.objects.get(id=countryId).region_id

    admins = UserRegion.objects.filter(region_id=regionId).values_list('user__email', flat=True)
    return admins


def send_notification_create(token, username, is_staff, email):
    email_context = {
        'confirmation_link': 'https://%s/verify_email/?token=%s&user=%s' % (
            settings.BASE_URL,  # on PROD it should point to goadmin...
            token,
            username,
        )
    }

    # if validated email accounts get a different message
    if is_staff:
        template = 'email/registration/verify-staff-email.html'
    else:
        template = 'email/registration/verify-outside-email.html'

    send_notification(
        'Validate your account',
        [email],
        render_to_string(template, email_context),
        'Validate account - ' + username
    )
