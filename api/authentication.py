from datetime import datetime, timedelta
from tastypie.authentication import ApiKeyAuthentication
import pytz

token_duration = timedelta(7)

class ExpiringApiKeyAuthentication(ApiKeyAuthentication):
    def get_key(self, user, api_key):
        """
        Attempts to find the API key for the user. Deletes it if it's
        older than 7 days.
        """
        from tastypie.models import ApiKey

        try:
            api_key = ApiKey.objects.get(user=user, key=api_key)
            current_time = datetime.utcnow()
            current_time = current_time.replace(tzinfo=pytz.utc)

            if not (current_time - api_key.created) < token_duration:
                api_key.delete()
                return self._unauthorized()
            else:
                api_key.created = current_time
                api_key.save()

        except ApiKey.DoesNotExist:
            return self._unauthorized()

        return True
