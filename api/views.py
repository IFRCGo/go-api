import json
import pytz

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views import View
from django.db.models.functions import Lower, TruncMonth, TruncYear
from django.db.models import Count, Sum
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
from registrations.models import Recovery
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
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, True) # deletePrevious
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not create one or more subscription(s), aborting'
            })
        return Response({ 'data': 'Success' })


class AddSubscription(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        errors, created = Subscription.sync_user_subscriptions(self.request.user, request.data, False) # do not deletePrevious ones, add only 1 subscription
        if len(errors):
            return Response({
                'status': 400,
                'data': 'Could not add subscription, aborting'
            })
        return Response({ 'data': 'Success' })

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
        return Response({ 'data': 'Success' })

class PublicJsonRequestView(View):
    http_method_names = ['get', 'head', 'options']
    def handle_get(self, request, *args, **kwargs):
        print(pretty_request(request))

    def get(self, request, *args, **kwargs):
        return self.handle_get(request, *args, **kwargs)


class EsPageHealth(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        health = ES_CLIENT.cluster.health()
        return JsonResponse(health)


class EsPageSearch(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
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


class AreaAggregate(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        region_type = request.GET.get('type', None)
        region_id = request.GET.get('id', None)

        if region_type not in ['country', 'region']:
            return bad_request('`type` must be `country` or `region`')
        elif not region_id:
            return bad_request('`id` must be a region id')

        aggregate = Appeal.objects.filter(**{region_type:region_id}) \
                                  .annotate(count=Count('id')) \
                                  .aggregate(Sum('num_beneficiaries'), Sum('amount_requested'), Sum('amount_funded'), Sum('count'))

        return JsonResponse(dict(aggregate))


class AggregateByDtype(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        models = {
            'appeal': Appeal,
            'event': Event,
            'fieldreport': FieldReport,
            'heop': Heop,
        }
        mtype = request.GET.get('model_type', None)
        if mtype is None or not mtype in models:
            return bad_request('Must specify an `model_type` that is `heop`, `appeal`, `event`, or `fieldreport`')

        model = models[mtype]
        aggregate = model.objects \
                         .values('dtype') \
                         .annotate(count=Count('id')) \
                         .order_by('count') \
                         .values('dtype', 'count')

        return JsonResponse(dict(aggregate=list(aggregate)))


class AggregateByTime(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
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

        if mtype is None or not mtype in models:
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

        filter_obj = { date_filter + '__gte': start_date }

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


@method_decorator(csrf_exempt, name='dispatch')
class PublicJsonPostView(View):
    http_method_names = ['post']
    def decode_auth_header(self, auth_header):
        parts = auth_header[7:].split(':')
        return parts[0], parts[1]

    def get_authenticated_user(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        # Parse the authorization header
        username, key = self.decode_auth_header(auth_header)
        if not username or not key:
            return None

        # Query the user
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return None

        # Query the key
        try:
            Token.objects.get(user=user, key=key)
        except ObjectDoesNotExist:
            return None

        return user


    def handle_post(self, request, *args, **kwargs):
        print(pretty_request(request))

    def post(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE').find('application/json') == -1:
            return bad_request('Content-type must be `application/json`')
        return self.handle_post(request, *args, **kwargs)


class GetAuthToken(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        if not 'username' in body or not 'password' in body:
            return bad_request('Body must contain `username` and `password`')
        username = body['username']
        password = body['password']

        #allowing different lower/uppercase lettered usernames:
        try:
            case_sensitive_username = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            case_sensitive_username = None

        user = authenticate(username=case_sensitive_username, password=password)

        if user is not None:
            api_key, created = Token.objects.get_or_create(user=user)

            # reset the key's created_at time each time we get new credentials
            if not created:
                api_key.created = datetime.utcnow().replace(tzinfo=pytz.utc)
                api_key.save()

            return JsonResponse({
                'token': api_key.key,
                'username': username,
                'first': user.first_name,
                'last': user.last_name,
                'expires': api_key.created + timedelta(7),
                'id': user.id,
            })
        else:
            return bad_request('Could not authenticate')


class ChangePassword(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        if not 'username' in body or (not 'password' in body and not 'token' in body):
            return bad_request('Must include a `username` and either a `password` or `token`')

        try:
            user = User.objects.get(username__iexact=body['username'])
        except ObjectDoesNotExist:
            return bad_request('Could not authenticate')

        if 'password' in body and not user.check_password(body['password']):
            return bad_request('Could not authenticate')
        elif 'token' in body:
            try:
                recovery = Recovery.objects.get(user=user)
            except ObjectDoesNotExist:
                return bad_request('Could not authenticate')

            if recovery.token != body['token']:
                return bad_request('Could not authenticate')
            recovery.delete()

        # TODO validate password
        if not 'new_password' in body:
            return bad_request('Must include a `new_password` property')

        user.set_password(body['new_password'])
        user.save()

        return JsonResponse({'status': 'ok'})


class RecoverPassword(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        if not 'email' in body:
            return bad_request('Must include an `email` property')

        try:
            req_email = body['email'].lower()
            user = User.objects.annotate(email_lower=Lower('email')).get(email_lower=req_email)
        except ObjectDoesNotExist:
            return bad_request('That email is not associated with a user')

        token = get_random_string(length=32)
        Recovery.objects.filter(user=user).delete()
        recovery = Recovery.objects.create(user=user,
                                           token=token)
        email_context = {
            'frontend_url': frontend_url,
            'username': user.username,
            'token': token
        }
        send_notification('Reset your password',
                          [user.email],
                          render_to_string('email/recover_password.html', email_context))

        return JsonResponse({'status': 'ok'})


class ShowUsername(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        if not 'email' in body:
            return bad_request('Must include an `email` property')

        try:
            req_email = body['email'].lower()
            user = User.objects.annotate(email_lower=Lower('email')).get(email_lower=req_email)
        except ObjectDoesNotExist:
            return bad_request('That email is not associated with a user')

        email_context = {
            'username': user.username,
        }
        send_notification('Showing your username',
                          [user.email],
                          render_to_string('email/show_username.html', email_context))

        return JsonResponse({'status': 'ok'})


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
        return Response({ 'data': 'Success' })


class DummyHttpStatusError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=500)


class DummyExceptionError(View):
    def get(self, request, *args, **kwargs):
        raise Exception('Dev raised exception!')
