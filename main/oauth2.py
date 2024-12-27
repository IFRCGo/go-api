from django.contrib.auth.models import User
from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):

    def get_additional_claims(self, request):
        user: User = request.user
        user.get_full_name()
        return {
            "sub": user.email,
            "email": user.email,
            "name": user.get_full_name(),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
