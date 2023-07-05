from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView

from api.views import (
    bad_http_request,
)
from notifications.notification import send_notification
from .models import Pending
from .utils import (
    is_valid_domain,
    getRegionalAdmins
)


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
        if pending_user.created_at < timezone.now() - timedelta(days=30):
            return bad_http_request('This link is expired',
                                    'You must verify your email within 30 days. \
                                    Please contact your system administrator.')

        if is_valid_domain(pending_user.user.email):
            pending_user.user.is_active = True
            pending_user.user.save()
            pending_user.delete()
            email_context = {
                'frontend_url': settings.FRONTEND_URL
            }
            return HttpResponse(render_to_string('registration/success.html', email_context))
        else:

            admins = getRegionalAdmins(pending_user.user_id)

            for admin in admins:
                token = pending_user.admin_token_1
                email_context = {
                    'validation_link': 'https://%s/validate_user/?token=%s&user=%s' % (
                        settings.BASE_URL,  # on PROD it should point to goadmin...
                        token,
                        user,
                    ),
                    'first_name': pending_user.user.first_name,
                    'last_name': pending_user.user.last_name,
                    'username': pending_user.user.username,
                    'email': pending_user.user.email,
                    'region': pending_user.user.profile.country.region,
                    'country': pending_user.user.profile.country,
                    'organization': pending_user.user.profile.org,
                    'city': pending_user.user.profile.city,
                    'department': pending_user.user.profile.department,
                    'position': pending_user.user.profile.position,
                    'phone': pending_user.user.profile.phone_number,
                    'justification': pending_user.justification,
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

        did_validate = getattr(pending_user, 'admin_1_validated')

        if did_validate:
            return bad_http_request('Already confirmed',
                                    'You have already confirmed this user.')

        setattr(pending_user, 'admin_1_validated', True)
        setattr(pending_user, 'admin_1_validated_date', timezone.now())
        pending_user.save()

        if pending_user.admin_1_validated:  # and pending_user.admin_2_validated:
            pending_user.user.is_active = True
            pending_user.user.save()
            email_context = {
                'frontend_url': settings.FRONTEND_URL
            }
            send_notification(
                'Your account has been approved',
                [pending_user.user.email],
                render_to_string('email/registration/outside-email-success.html', email_context),
                f'Approved account successfully - {pending_user.user.username}'
            )
            pending_user.delete()
            return HttpResponse(render_to_string('registration/validation-success.html'))
