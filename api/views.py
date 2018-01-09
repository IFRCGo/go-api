import json

from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views import View
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Count, Sum
from django.utils import timezone

from tastypie.models import ApiKey
from .utils import pretty_request
from .authentication import token_duration
from .esconnection import ES_CLIENT
from .models import Appeal, Event, FieldReport
from deployments.models import Heop
from notifications.models import Subscription


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


class PublicJsonRequestView(View):
    http_method_names = ['get', 'head', 'options']
    def handle_get(self, request, *args, **kwargs):
        print(pretty_request(request))

    def get(self, request, *args, **kwargs):
        return self.handle_get(request, *args, **kwargs)


class EsPageSearch(PublicJsonRequestView):
    def handle_get(self, request, *args, **kwargs):
        page_type = request.GET.get('type', None)
        phrase = request.GET.get('keyword', None)
        if phrase is None:
            return bad_request('Must include a `keyword`')
        if page_type is None:
            page_type = '*'
        index = 'page_%s' % page_type
        query = {
            'bool': {
                'must': {'prefix': {'name': phrase }}
            }
        }
        results = ES_CLIENT.search(
            index=index,
            doc_type='page',
            body=json.dumps({'query': query}),
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

        trunc_method = TruncMonth if unit == 'month' else TruncYear

        aggregate = model.objects \
                         .filter(**filter_obj) \
                         .annotate(timespan=trunc_method(date_filter, tzinfo=timezone.utc)) \
                         .values('timespan') \
                         .annotate(count=Count('id')) \
                         .order_by('timespan') \
                         .values('timespan', 'count')

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
        except User.DoesNotExist:
            return None

        # Query the key
        try:
            ApiKey.objects.get(user=user, key=key)
        except ApiKey.DoesNotExist:
            return None

        return user


    def handle_post(self, request, *args, **kwargs):
        print(pretty_request(request))

    def post(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE') != 'application/json':
            return bad_request('Content-type must be `application/json`')
        return self.handle_post(request, *args, **kwargs)


class GetAuthToken(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        print(pretty_request(request))
        body = json.loads(request.body.decode('utf-8'))
        username = body['username']
        password = body['password']
        if not username or not password:
            return bad_request('Body must contain `username` and `password`')

        user = authenticate(username=username, password=password)
        if user is not None:
            api_key, created = ApiKey.objects.get_or_create(user=user)
            return JsonResponse({
                'token': api_key.key,
                'username': username,
                'first': user.first_name,
                'last': user.last_name,
                'expires': api_key.created + token_duration,
                'id': user.id,
            })
        else:
            return bad_request('Could not authenticate')


class UpdateSubscriptionPreferences(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        user = self.get_authenticated_user(request)
        if not user:
            return unauthorized()

        body = json.loads(request.body.decode('utf-8'))
        errors, created = Subscription.sync_user_subscriptions(user, body)
        if len(errors):
            return JsonResponse({
                'statusCode': 400,
                'error_message': 'Could not create one or more subscription(s), aborting',
                'errors': errors
            }, status=400)
        else:
            return JsonResponse({'statusCode': 200, 'created': len(created)})
