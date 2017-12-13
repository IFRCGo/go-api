import base64
from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie.models import ApiKey


# overwrite is_authenticated to check api key
class PublicModelResource(ModelResource):

    def get_authorization_data(self, request):
        authorization = request.META.get('HTTP_AUTHORIZATION', '')
        if not authorization:
            raise ValueError('Authorization header missing or empty.')

        try:
            auth_type, data = authorization.split(' ', 1)
        except:
            raise ValueError('Authorization header must have a space separating auth_type and data.')

        if auth_type.lower() != 'apikey':
            raise ValueError('auth_type is not "ApiKey".')

        return data

    def extract_credentials(self, request):
        data = self.get_authorization_data(request)
        username, password = data.split(':', 1)
        return username, password

    def get_key(self, user, api_key):
        try:
            if user.api_key.key != api_key:
                return False
        except ApiKey.DoesNotExist:
            return False
        return True

    def has_valid_api_key(self, request, **kwargs):
        try:
            username, api_key = self.extract_credentials(request)
        except ValueError:
            return False

        if not username or not api_key:
            return False

        try:
            user = User.objects.select_related('api_key').get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return False

        key_auth_check = self.get_key(user, api_key)
        if key_auth_check:
            request.user = user

        return key_auth_check
