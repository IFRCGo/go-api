import pytz
from django.db.models import Q
from django.db.models.functions import Lower
from datetime import timedelta, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from api.views import (
    bad_request,
    bad_http_request,
)
from api.models import Country
from .models import Pending, DomainWhitelist
from notifications.notification import send_notification
from main.frontend import frontend_url


def is_valid_domain(email):
    domain = email.lower().split('@')[1]
    is_allowed = (
        DomainWhitelist.objects
                       .filter(is_active=True)
                       .annotate(domain_name_lower=Lower('domain_name'))
                       .filter(domain_name_lower=domain)
                       .exists()
    )

    if is_allowed or domain in ['ifrc.org', 'arcs.org.af', 'voroskereszt.hu']:
        return True
    return False


def get_valid_admins(contacts):
    if not type(contacts) is list:
        return False
    emails = [admin.get('email', None) for admin in contacts]
    if len(emails) < 1:
        return False
    admin_users = User.objects.filter(email__in=emails)
    if admin_users.count() != len(emails):
        return False
    return emails


def create_inactive_user(username, firstname, lastname, email, password):
    user = User.objects.create_user(username=username,
                                    first_name=firstname,
                                    last_name=lastname,
                                    email=email,
                                    password=password,
                                    is_active=False)
    return user


def set_user_profile(user, country, organization_type, organization, city, department, position, phone_number):
    user.profile.country = Country.objects.get(pk=country)
    user.profile.org_type = organization_type
    user.profile.org = organization
    user.profile.city = city
    user.profile.department = department
    user.profile.position = position
    user.profile.phone_number = phone_number
    user.save()
    return user


class NewRegistration(APIView):
    permission_classes = []

    def post(self, request):
        required_fields = (
            'email',
            'username',
            'password',
            'country',
            'organizationType',
            'organization',
            'firstname',
            'lastname',
        )

        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        email = request.data.get('email', None)
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        firstname = request.data.get('firstname', None)
        lastname = request.data.get('lastname', None)
        country = request.data.get('country', None)
        city = request.data.get('city', None)
        organization_type = request.data.get('organizationType', None)
        organization = request.data.get('organization', None)
        department = request.data.get('department', None)
        position = request.data.get('position', None)
        phone_number = request.data.get('phoneNumber', None)
        contact = request.data.get('contact', None)

        is_staff = is_valid_domain(email)
        admins = True if is_staff else get_valid_admins(contact)
        if not admins:
            return bad_request('Non-IFRC users must submit two valid admin emails.')
        if User.objects.filter(email__iexact=email).exists():
            return bad_request('A user with that email address already exists.')
        if User.objects.filter(username__iexact=username).exists():
            return bad_request('That username is taken, please choose a different one.')
        if ' ' in username:
            return bad_request('Username can not contain spaces, please choose a different one.')

        # Create the User object
        try:
            user = create_inactive_user(username, firstname, lastname, email, password)
        except Exception:
            return bad_request('Could not create user.')

        # Set the User Profile properties
        try:
            set_user_profile(user, country, organization_type, organization, city, department, position, phone_number)
        except Exception:
            User.objects.filter(username=username).delete()
            return bad_request('Could not create user profile.')

        pending = Pending.objects.create(user=user,
                                         token=get_random_string(length=32))
        if not is_staff:
            pending.admin_contact_1 = admins[0]
            pending.admin_contact_2 = admins[1]
            pending.admin_token_1 = get_random_string(length=32)
            pending.admin_token_2 = get_random_string(length=32)
            pending.admin_1_validated = False
            pending.admin_2_validated = False

        pending.save()

        email_context = {
            'confirmation_link': 'https://%s/verify_email/?token=%s&user=%s' % (
                settings.BASE_URL,  # on PROD it should point to goadmin...
                pending.token,
                username,
            )
        }

        # if validated email accounts get a different message
        if is_staff:
            template = 'email/registration/verify-staff-email.html'
        else:
            template = 'email/registration/verify-outside-email.html'

        send_notification('Validate your account',
                          [email],
                          render_to_string(template, email_context),
                          'Validate account - ' + username)

        return JsonResponse({'status': 'ok'})


class VerifyEmail(APIView):
    def get(self, request):
        token = request.GET.get('token', None)
        user = request.GET.get('user', None)
        if not token or not user:
            return bad_http_request('Credentials not found',
                                    'The URL must include a token and user. \
                                    Please check your verification email and try again. \
                                    If this problem persists, contact a system administrator.')

        try:
            pending_user = Pending.objects.get(token=token, user__username=user)
        except ObjectDoesNotExist:
            return bad_http_request('User not found, or token incorrect',
                                    'We could not find a user and token that matched those supplied. \
                                    Please contact your system administrator.')

        if pending_user.user.is_active:
            return bad_http_request('%s is active' % user,
                                    'The user is already active. If you need to reset your password, \
                                    contact your system administrator.')
        if pending_user.email_verified:
            return bad_http_request('You have already verified your email',
                                    'A validation email has been sent to the administrators you listed.')
        if pending_user.created_at < datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=1):
            return bad_http_request('This link is expired',
                                    'You must verify your email within 24 hours. \
                                    Please contact your system administrator.')

        if is_valid_domain(pending_user.user.email):
            pending_user.user.is_active = True
            pending_user.user.save()
            pending_user.delete()
            email_context = {
                'frontend_url': frontend_url
            }
            return HttpResponse(render_to_string('registration/success.html', email_context))
        else:
            admins = [pending_user.admin_contact_1, pending_user.admin_contact_2]
            for idx, admin in enumerate(admins):
                token = pending_user.admin_token_1 if idx == 0 else pending_user.admin_token_2
                email_context = {
                    'validation_link': 'https://%s/validate_user/?token=%s&user=%s' % (
                        settings.BASE_URL,  # on PROD it should point to goadmin...
                        token,
                        user,
                    ),
                    'first_name': pending_user.user.first_name,
                    'last_name': pending_user.user.last_name,
                    'email': pending_user.user.email,
                }
                send_notification('Reference to approve an account',
                                  [admin],
                                  render_to_string('email/registration/validate.html', email_context),
                                  'Approve an account - ' + pending_user.user.username)
            pending_user.email_verified = True
            pending_user.save()
            return HttpResponse(render_to_string('registration/validation-sent.html'))


class ValidateUser(APIView):
    def get(self, request):
        token = request.GET.get('token', None)
        user = request.GET.get('user', None)
        if not token or not user:
            return bad_http_request('Credentials not found',
                                    'The URL must include a token and user. Please check your email and try again.')
        try:
            pending_user = Pending.objects.get(Q(admin_token_1=token) | Q(admin_token_2=token), user__username=user)
        except ObjectDoesNotExist:
            return bad_http_request('User not found, or token incorrect',
                                    'We could not find a user and token that matched those supplied.')

        if pending_user.user.is_active:
            return bad_http_request('%s is active' % user,
                                    'The user is already active. \
                                    You can modify user accounts any time using the admin interface.')

        # Determine which admin we're responding to.
        admin = '1' if token == pending_user.admin_token_1 else '2'
        did_validate = getattr(pending_user, 'admin_%s_validated' % admin)

        if did_validate:
            return bad_http_request('Already confirmed',
                                    'You have already confirmed this user.')

        setattr(pending_user, 'admin_%s_validated' % admin, True)
        setattr(pending_user, 'admin_%s_validated_date' % admin, datetime.now())
        pending_user.save()

        if pending_user.admin_1_validated and pending_user.admin_2_validated:
            pending_user.user.is_active = True
            pending_user.user.save()
            email_context = {
                'frontend_url': frontend_url
            }
            send_notification('Your account has been approved',
                              [pending_user.user.email],
                              render_to_string('email/registration/outside-email-success.html', email_context),
                              'Approved account successfully - ' + pending_user.user.username)
            pending_user.delete()
            return HttpResponse(render_to_string('registration/validation-success.html'))
        else:
            return HttpResponse(render_to_string('registration/validation-halfsuccess.html'))
