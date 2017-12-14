from django.contrib import admin
import notifications.models as models


admin.site.register(models.SurgeAlert)
admin.site.register(models.Subscription)
