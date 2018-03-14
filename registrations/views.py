import json
import pytz
from datetime import timedelta, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from api.models import Country
from .models import Pending
from notifications.notification import send_notification
from main.frontend import frontend_url


def is_valid_domain(email):
    domain = email.lower().split('@')[1]
    allowed_list = [
        'ifrc.org',
        'apdisasterresilience.org',
        'arabrcrc.org',
        'arcs.org.af',
        'bdrcs.org',
        'cck-cr.cz',
        'ckcg.me',
        'climatecentre.org',
        'creuroja.ad',
        'cri.it',
        'croix-rouge.fr',
        'croix-rouge.lu',
        'croix-rouge.mc',
        'croixrouge.ht',
        'croixrougesenegal.com',
        'crucearosie.ro',
        'cruzroja.cl',
        'cruzroja.es',
        'cruzroja.gt',
        'cruzroja.or.cr',
        'cruzroja.org',
        'cruzroja.org.ar',
        'cruzroja.org.hn',
        'cruzroja.org.pa',
        'cruzroja.org.pe',
        'cruzroja.org.py',
        'cruzrojaboliviana.org',
        'cruzrojacolombiana.org',
        'cruzrojamexicana.org.mx',
        'cruzrojanicaraguense.org',
        'cruzrojasal.org.sv',
        'cruzrojauruguaya.org',
        'cruzrojavenezolana.org',
        'cruzvermelha.org.br',
        'cruzvermelha.pt',
        'drk.de',
        'drk.dk',
        'egyptianrc.org',
        'fijiredcross.org',
        'grsproadsafety.org',
        'guatemala.cruzroja.org',
        'hck.hr',
        'honduras.cruzroja.org',
        'icrc.org',
        'indianredcross.org',
        'jamaicaredcross.org',
        'jnrcs.org',
        'jrc.or.jp',
        'kenyaredcross.org',
        'kizilay.org.tr',
        'krcs.org.kw',
        'laoredcross.org.la',
        'livelihoodscentre.org',
        'mauritiusredcross.com',
        'mdais.org',
        'nrcs.org',
        'palestinercs.org',
        'pck.org.pl',
        'pmi.or.id',
        'prcs.org.pk',
        'pscentre.org',
        'qrcs.org.qa',
        'rcs.ir',
        'rcsbahrain.org',
        'rcuae.ae',
        'redcrescent.az',
        'redcrescent.kz',
        'redcrescent.org.mv',
        'redcrescent.org.my',
        'redcrescent.tj',
        'redcrescent.uz',
        'redcross-eu.net',
        'redcross.am',
        'redcross.be',
        'redcross.bg',
        'redcross.by',
        'redcross.ca',
        'redcross.ch',
        'redcross.ee',
        'redcross.fi',
        'redcross.ge',
        'redcross.gr',
        'redcross.ie',
        'redcross.int',
        'redcross.is',
        'redcross.lk',
        'redcross.lt',
        'redcross.lv',
        'redcross.md',
        'redcross.mn',
        'redcross.no',
        'redcross.or.ke',
        'redcross.or.kr',
        'redcross.or.th',
        'redcross.org',
        'redcross.org.au',
        'redcross.org.cn',
        'redcross.org.cy',
        'redcross.org.hk',
        'redcross.org.jm',
        'redcross.org.kh',
        'redcross.org.lb',
        'redcross.org.mm',
        'redcross.org.mo',
        'redcross.org.mt',
        'redcross.org.mz',
        'redcross.org.na',
        'redcross.org.nz',
        'redcross.org.ph',
        'redcross.org.rs',
        'redcross.org.sg',
        'redcross.org.ua',
        'redcross.org.uk',
        'redcross.org.vn',
        'redcross.org.za',
        'redcross.ru',
        'redcross.se',
        'redcross.sk',
        'redcross.tl',
        'redcrosseth.org',
        'redcrossmuseum.ch',
        'redcrossug.org',
        'redcrosszim.org.zw',
        'rks.si',
        'rodekors.dk',
        'rodekruis.nl',
        'redcross.nl',
        'roteskreuz.at',
        'roteskreuz.li',
        'sarc.sy',
        'sierraleoneredcross.org',
        'srcs.sd',
        'standcom.ch',
        'voroskereszt.hu'
    ]
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
                                    first_name=raw['firstname'],
                                    last_name=raw['lastname'],
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
        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'email',
            'username',
            'password',
            'country',
            'organizationType',
            'organization',
            'firstname',
            'lastname',
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        is_staff = is_valid_domain(body['email'])
        admins = True if is_staff else get_valid_admins(body['contact'])
        if not admins:
            return bad_request('Non-IFRC users must submit two valid admin emails.')
        if User.objects.filter(email=body['email']).count() > 0:
            return bad_request('A user with that email address already exists.')
        if User.objects.filter(username=body['username']).count() > 0:
            return bad_request('That username is taken, please choose a different one.')

        try:
            user = create_active_user(body)
        except:
            return bad_request('Could not create user.')

        try:
            # Note, this also sets the user's active status to False
            set_user_profile_inactive(user, body)
        except:
            User.objects.filter(username=body['username']).delete()
            return bad_request('Could not create user profile.')

        pending = Pending.objects.create(user=user,
                                         token=get_random_string(length=32))

        if not is_staff:
            pending.admin_contact_1 = admins[0]
            pending.admin_contact_2 = admins[1]
            pending.admin_token = get_random_string(length=32)

        pending.save()

        email_context = {
            'confirmation_link': '%s/verify_email/?token=%s&user=%s' % (
                settings.BASE_URL,
                pending.token,
                body['username'],
            )
        }

        # if validated email accounts get a different message
        if is_staff:
            template = 'email/registration/verify-staff-email.html'
        else:
            template = 'email/registration/verify-outside-email.html'

        send_notification('Validate your account',
                          [body['email']],
                          render_to_string(template, email_context))

        return JsonResponse({'status': 'ok'})


class VerifyEmail(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        token = request.GET.get('token', None)
        user = request.GET.get('user', None)
        if not token or not user:
            return bad_http_request('Credentials not found',
                                    'The URL must include a token and user. Please check your verification email and try again. If this problem persists, contact a system administrator.')

        try:
            pending_user = Pending.objects.get(token=token, user__username=user)
        except ObjectDoesNotExist:
            return bad_http_request('User not found, or token incorrect',
                                    'We could not find a user and token that matched those supplied. Please contact your system administrator.')

        if pending_user.user.is_active:
            return bad_http_request('%s is active' % user,
                                    'The user is already active. If you need to reset your password, contact your system administrator.')
        if pending_user.email_verified:
            return bad_http_request('You have already verified your email',
                                    'A validation email has been sent to the administrators you listed.')
        if pending_user.created_at < datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=1):
            return bad_http_request('This link is expired',
                                    'You must verify your email within 24 hours. Please contact your system administrator.')

        if is_valid_domain(pending_user.user.email):
            pending_user.user.is_active = True
            pending_user.user.save()
            pending_user.delete()
            return HttpResponse(render_to_string('registration/success.html'))
        else:
            admins = [pending_user.admin_contact_1, pending_user.admin_contact_2]
            email_context = {
                'validation_link': '%s/validate_user/?token=%s&user=%s' % (
                    settings.BASE_URL,
                    pending_user.admin_token,
                    user,
                ),
                'first_name': pending_user.user.first_name,
                'last_name': pending_user.user.last_name,
                'email': pending_user.user.email,
            }
            send_notification('Reference to approve an account',
                              admins,
                              render_to_string('email/registration/validate.html', email_context))
            pending_user.email_verified = True
            pending_user.save()
            return HttpResponse(render_to_string('registration/validation-sent.html'))


class ValidateUser(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        token = request.GET.get('token', None)
        user = request.GET.get('user', None)
        if not token or not user:
            return bad_http_request('Credentials not found',
                                    'The URL must include a token and user. Please check your email and try again.')
        try:
            pending_user = Pending.objects.get(admin_token=token, user__username=user)
        except ObjectDoesNotExist:
            return bad_http_request('User not found, or token incorrect',
                                    'We could not find a user and token that matched those supplied.')

        if pending_user.user.is_active:
            return bad_http_request('%s is active' % user,
                                    'The user is already active. You can modify user accounts any time using the admin interface.')

        pending_user.user.is_active = True
        pending_user.user.save()
        email_context = {
            frontend_url: frontend_url
        }
        send_notification('Your account has been approved',
                          [pending_user.user.email],
                          render_to_string('email/registration/outside-email-success.html', email_context))
        pending_user.delete()
        return HttpResponse(render_to_string('registration/validation-success.html'))
