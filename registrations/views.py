import json
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.template.loader import render_to_string
from api.views import bad_request, PublicJsonPostView, PublicJsonRequestView
from api.utils import pretty_request
from api.models import Country
from .models import Pending
from notifications.notification import send_notification


def is_valid_domain(email):
    domain = email.lower().split('@')[1]
    allowed_list = ['ifrc.org']
    if domain in allowed_list:
        return True
    return False


def get_valid_admins(contacts):
    if not type(contacts) is list:
        return False
    emails = [admin['email'] for admin in contacts if admin['email'] is not None]
    if len(emails) < 1:
        return False
    admin_users = User.objects.filter(email__in=emails)
    if admin_users.count() != len(emails):
        return False
    return emails


def create_active_user(raw):
    user = User.objects.create_user(username=raw['username'],
                                    email=raw['email'],
                                    password=raw['password'])
    return user


def set_user_profile_inactive(user, raw):
    user.is_active = False
    user.profile.country = Country.objects.get(pk=raw['country'])
    user.profile.org_type = raw['organizationType']
    user.profile.org = raw['organization']
    user.profile.city = raw['city'] if 'city' in raw else None
    user.profile.department = raw['department'] if 'department' in raw else None
    user.profile.position = raw['position'] if 'position' in raw else None
    user.profile.phone_number = raw['phoneNumber'] if 'phoneNumber' in raw else None
    user.save()
    return user


class NewRegistration(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        print(pretty_request(request))
        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'email',
            'username',
            'password',
            'country',
            'organizationType',
            'organization',
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        is_staff = is_valid_domain(body['email'])
        admins = True if is_staff else get_valid_admins(body['contact'])
        if not admins:
            return bad_request('Non-IFRC users must submit two valid admin emails')

        try:
            user = create_active_user(body)
        except:
            return bad_request('Could not create user')

        try:
            # Note, this also sets the user's active status to False
            set_user_profile_inactive(user, body)
        except:
            User.objects.filter(username=body['username']).delete()
            return bad_request('Could not create user profile')

        pending = Pending.objects.create(user=user,
                                         token=get_random_string(length=32))

        if not is_staff:
            pending.admin_1 = admins[0]
            pending.admin_2 = admins[1]

        pending.save()

        email_context = {
            'confirmation_link': '%s/verify_email/?token=%s' % (settings.BASE_URL,
                                                                pending.token)
        }

        send_notification('Please verify your email address',
                          [body['email']],
                          render_to_string('email/verify_email.html', email_context))

        return JsonResponse({'status': 'ok'})
