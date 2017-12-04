from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from .models import SurgeAlert

class SurgeAlertResource(ModelResource):
    def dehydrate_message(self, bundle):
        if self.is_authenticated(bundle.request):
            return bundle.data['summary']
        else:
            return 'You must be logged in to read private notifications'

    class Meta:
        queryset = SurgeAlert.objects.all()
        resource_name = 'surge_alert'
        allowed_methods = ['get']
        authorization = Authorization()
