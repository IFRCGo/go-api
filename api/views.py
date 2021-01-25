import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.views import View
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models.fields import IntegerField
from django.db.models import Count, Sum, Q, F, Case, When
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string

from rest_framework.authtoken.models import Token
from .utils import pretty_request
from .esconnection import ES_CLIENT
from .models import Appeal, Event, FieldReport, CronJob
from .indexes import ES_PAGE_NAME
from deployments.models import Heop
from notifications.models import Subscription
from notifications.notification import send_notification
from registrations.models import Recovery, Pending
from main.frontend import frontend_url


def bad_request(message):
    return JsonResponse({
        'statusCode': 400,
        'error_message': message
    }, status=400)


def bad_http_request(header, message):
    return HttpResponse('<h2>%s</h2><p>%s</p>' % (header, message), status=400)


def unauthorized(message='You must be logged in'):
    return JsonResponse({
        'statusCode': 401,
        'error_message': message
    }, status=401)


class UpdateSubscriptionPreferences(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, True)  # deletePrevious
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not create one or more subscription(s), aborting'
            })
        return Response({'data': 'Success'})


class AddSubscription(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # do not delete previous ones, add only 1 subscription
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, False)
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not add subscription, aborting'
            })
        return Response({'data': 'Success'})


class DelSubscription(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors = Subscription.del_user_subscriptions(self.request.user, request.data)
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not remove subscription, aborting'
            })
        return Response({'data': 'Success'})


class EsPageHealth(APIView):
    def get(self, request):
        health = ES_CLIENT.cluster.health()
        return JsonResponse(health)


class EsPageSearch(APIView):
    def get(self, request):
        page_type = request.GET.get('type', None)
        phrase = request.GET.get('keyword', None)
        if phrase is None:
            return bad_request('Must include a `keyword`')
        index = ES_PAGE_NAME
        query = {
            'multi_match': {
                'query': phrase,
                'fields': ['keyword^3', 'body']
            }
        }

        sort = [
            {'date': {'order': 'desc', 'missing': '_first'}},
            '_score',
        ]

        if page_type is not None:
            query = {
                'bool': {
                    'filter': {
                        'term': {'type': page_type}
                    },
                    'must': {
                        'multi_match': query['multi_match']
                    }
                }
            }

        results = ES_CLIENT.search(
            index=index,
            doc_type='page',
            body=json.dumps({
                'query': query,
                'sort': sort,
                'from': 0,
                'size': 10
            })
        )
        return JsonResponse(results['hits'])


class AggregateHeaderFigures(APIView):
    def get(self, request):
        now = timezone.now()
        appeal_conditions = (Q(atype=1) | Q(atype=2)) & Q(end_date__gt=now)
        appeals_aggregated = Appeal.objects.annotate(
            # Active Appeals with DREF type
            actd=Count(Case(
                When(Q(atype=0) & Q(end_date__gt=now), then=1),
                output_field=IntegerField()
            )),
            # Active Appeals with type Emergency Appeal or International Appeal
            acta=Count(Case(
                When(appeal_conditions, then=1),
                output_field=IntegerField()
            )),
            # Total Appeals count which are not DREF
            tota=Count(Case(
                When(Q(atype=1) | Q(atype=2), then=1),
                output_field=IntegerField()
            )),
            # Active Appeals' target population
            tarp=Sum(Case(
                When(Q(end_date__gt=now), then=F('num_beneficiaries')),
                output_field=IntegerField()
            )),
            # Active Appeals' requested amount, which are not DREF
            amor=Case(
                When(appeal_conditions, then=F('amount_requested')),
                output_field=IntegerField()
            ),
            # Active Appeals' funded amount, which are not DREF
            amof=Case(
                When(appeal_conditions, then=F('amount_funded')),
                output_field=IntegerField()
            )
        ).aggregate(
            active_drefs=Sum('actd'),
            active_appeals=Sum('acta'),
            total_appeals=Sum('tota'),
            target_population=Sum('tarp'),
            amount_requested=Sum('amor'),
            amount_funded=Sum('amof')
        )

        return JsonResponse(dict(appeals_aggregated))


class AreaAggregate(APIView):
    def get(self, request):
        region_type = request.GET.get('type', None)
        region_id = request.GET.get('id', None)

        if region_type not in ['country', 'region']:
            return bad_request('`type` must be `country` or `region`')
        elif not region_id:
            return bad_request('`id` must be a region id')

        aggregate = Appeal.objects\
            .filter(**{region_type: region_id}) \
            .annotate(count=Count('id')) \
            .aggregate(Sum('num_beneficiaries'), Sum('amount_requested'), Sum('amount_funded'), Sum('count'))

        return JsonResponse(dict(aggregate))


class AggregateByDtype(APIView):
    def get(self, request):
        models = {
            'appeal': Appeal,
            'event': Event,
            'fieldreport': FieldReport,
            'heop': Heop,
        }
        mtype = request.GET.get('model_type', None)
        if mtype is None or mtype not in models:
            return bad_request('Must specify an `model_type` that is `heop`, `appeal`, `event`, or `fieldreport`')

        model = models[mtype]
        aggregate = model.objects \
                         .values('dtype') \
                         .annotate(count=Count('id')) \
                         .order_by('count') \
                         .values('dtype', 'count')

        return JsonResponse(dict(aggregate=list(aggregate)))


class AggregateByTime(APIView):
    def get(self, request):
        models = {
            'appeal': Appeal,
            'event': Event,
            'fieldreport': FieldReport,
            'heop': Heop,
        }

        unit = request.GET.get('unit', None)
        start_date = request.GET.get('start_date', None)
        mtype = request.GET.get('model_type', None)

        country = request.GET.get('country', None)
        region = request.GET.get('region', None)

        if mtype is None or mtype not in models:
            return bad_request('Must specify an `model_type` that is `heop`, `appeal`, `event`, or `fieldreport`')

        if start_date is None:
            start_date = datetime(1980, 1, 1, tzinfo=timezone.utc)
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                return bad_request('`start_date` must be YYYY-MM-DD format')

            start_date = start_date.replace(tzinfo=timezone.utc)

        model = models[mtype]

        # set date filter property
        date_filter = 'created_at'
        if mtype == 'appeal' or mtype == 'heop':
            date_filter = 'start_date'
        elif mtype == 'event':
            date_filter = 'disaster_start_date'

        filter_obj = {date_filter + '__gte': start_date}

        # useful shortcut for singular/plural location filters
        is_appeal = True if mtype == 'appeal' else False

        # set country and region filter properties
        if country is not None:
            country_filter = 'country' if is_appeal else 'countries__in'
            countries = country if is_appeal else [country]
            filter_obj[country_filter] = countries
        elif region is not None:
            region_filter = 'region' if is_appeal else 'regions__in'
            regions = region if is_appeal else [region]
            filter_obj[region_filter] = regions

        # allow custom filter attributes
        # TODO this should check if the model definition contains this field
        for key, value in request.GET.items():
            if key[0:7] == 'filter_':
                filter_obj[key[7:]] = value

        # allow arbitrary SUM functions
        annotation_funcs = {
            'count': Count('id')
        }
        output_values = ['timespan', 'count']
        for key, value in request.GET.items():
            if key[0:4] == 'sum_':
                annotation_funcs[key[4:]] = Sum(value)
                output_values.append(key[4:])

        trunc_method = TruncMonth if unit == 'month' else TruncYear

        aggregate = model.objects \
                         .filter(**filter_obj) \
                         .annotate(timespan=trunc_method(date_filter, tzinfo=timezone.utc)) \
                         .values('timespan') \
                         .annotate(**annotation_funcs) \
                         .order_by('timespan') \
                         .values(*output_values)

        return JsonResponse(dict(aggregate=list(aggregate)))


class GetAuthToken(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)

        if username is None or password is None:
            return bad_request('Body must contain `email/username` and `password`')

        user = authenticate(username=username, password=password)
        if user is not None:
            api_key, created = Token.objects.get_or_create(user=user)

            # Reset the key's created_at time each time we get new credentials
            if not created:
                api_key.created = timezone.now()
                api_key.save()

            # (Re)set the user's last frontend login datetime
            user.profile.last_frontend_login = timezone.now()
            user.profile.save()

            return JsonResponse({
                'token': api_key.key,
                'username': username,
                'first': user.first_name,
                'last': user.last_name,
                'expires': api_key.created + timedelta(7),
                'id': user.id,
            })
        else:
            return bad_request('Invalid username or password')  # most probably password issue


class ChangePassword(APIView):
    permissions_classes = []

    def post(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        new_pass = request.data.get('new_password', None)
        token = request.data.get('token', None)
        # 'password' is checked for Change Password, 'token' is checked for Password Recovery
        if username is None or (password is None and token is None):
            return bad_request('Must include a `username` and either a `password` or `token`')

        if new_pass is None:
            return bad_request('Must include a `new_password` property')
        try:
            validate_password(new_pass)
        except Exception as exc:
            ers = ' '.join(str(err) for err in exc)
            return bad_request(ers)

        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            return bad_request('Could not authenticate')

        if password and not user.check_password(password):
            return bad_request('Could not authenticate')
        elif token:
            recovery = Recovery.objects.filter(user=user).first()
            if recovery is None:
                return bad_request('Could not authenticate')

            if recovery.token != token:
                return bad_request('Could not authenticate')
            recovery.delete()

        user.set_password(new_pass)
        user.save()

        return JsonResponse({'status': 'ok'})


class RecoverPassword(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', None)
        if email is None:
            return bad_request('Must include an `email` property')

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return bad_request('That email is not associated with a user')

        token = get_random_string(length=32)
        Recovery.objects.filter(user=user).delete()
        Recovery.objects.create(user=user, token=token)
        email_context = {
            'frontend_url': frontend_url,
            'username': user.username,
            'token': token
        }
        send_notification('Reset your password',
                          [user.email],
                          render_to_string('email/recover_password.html', email_context),
                          'Password recovery - ' + user.username)

        return JsonResponse({'status': 'ok'})


class ShowUsername(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', None)
        if email is None:
            return bad_request('Must include an `email` property')

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return bad_request('That email is not associated with a user')

        email_context = {
            'username': user.username,
        }
        send_notification('Showing your username',
                          [user.email],
                          render_to_string('email/show_username.html', email_context),
                          'Username recovery - ' + user.username)

        return JsonResponse({'status': 'ok'})


class ResendValidation(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username', None)

        if username:
            # Now we allow requesting with either email or username
            pending_user = Pending.objects.select_related('user')\
                                          .filter(Q(user__username__iexact=username) | Q(user__email__iexact=username))\
                                          .first()
            if pending_user:
                if pending_user.user.is_active is True:
                    return bad_request('Your registration is already active, \
                                        you can try logging in with your registered username and password')
                if pending_user.created_at < timezone.now() - timedelta(days=1):
                    return bad_request('The verification period is expired. \
                                        You must verify your email within 24 hours. \
                                        Please contact your system administrator.')

                # Construct and re-send the email
                email_context = {
                    'confirmation_link': 'https://%s/verify_email/?token=%s&user=%s' % (
                        settings.BASE_URL,  # on PROD it should point to goadmin...
                        pending_user.token,
                        username,
                    )
                }

                if pending_user.user.is_staff:
                    template = 'email/registration/verify-staff-email.html'
                else:
                    template = 'email/registration/verify-outside-email.html'

                send_notification('Validate your account',
                                  [pending_user.user.email],
                                  render_to_string(template, email_context),
                                  'Validate account - ' + username)
                return Response({'data': 'Success'})
            else:
                return bad_request('No pending registration found with the provided username. \
                                    Please check your input.')
        else:
            return bad_request('Please provide your username in the request.')


class AddCronJobLog(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        errors, created = CronJob.sync_cron(request.data)
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not add CronJob, aborting'
            })
        return Response({'data': 'Success'})


class DummyHttpStatusError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=500)


class DummyExceptionError(View):
    def get(self, request, *args, **kwargs):
        raise Exception('Dev raised exception!')
