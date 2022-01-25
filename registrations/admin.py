from django.contrib import admin
from api.logger import logger
from api.models import User, UserRegion, Country, Profile
import registrations.models as models
from reversion_compare.admin import CompareVersionAdmin
from notifications.notification import send_notification
from django.template.loader import render_to_string
from main.frontend import frontend_url


class PendingAdmin(CompareVersionAdmin):
    readonly_fields = ('created_at','user','justification')
    search_fields = ('user__username', 'user__email', 'admin_contact_1', 'admin_contact_2')
    list_display = ('get_username_and_mail', 'created_at', 'email_verified', 'user_is_active')
    actions = ('activate_users',)
    
    # Get the 'user' objects with a JOIN query
    def get_queryset(self, request):
        if request.user.is_superuser:
            retval = super().get_queryset(request).select_related('user')
        else:
            region_id = UserRegion.objects.filter(user_id=request.user.id).values_list('region_id', flat=True)
            country_ids = Country.objects.filter(region_id__in=region_id).values_list('id', flat=True)
            user_ids = Profile.objects.filter(country_id__in=country_ids).values_list('user_id', flat=True)

            retval = super().get_queryset(request).select_related('user').filter(user_id__in=user_ids)

        return retval
         
    def get_username_and_mail(self, obj):
        return obj.user.username + ' - ' + obj.user.email

    def user_is_active(self, obj):
        return 'Yes' if obj.user.is_active else ''

    def activate_users(self, request, queryset):
        for pu in queryset:
            usr = User.objects.filter(id=pu.user_id).first()
            if usr:
                if usr.is_active is False:
                    
                    email_context = {
                        'frontend_url': frontend_url
                    }

                    send_notification('Your account has been approved',
                              [usr.email],
                              render_to_string('email/registration/outside-email-success.html', email_context),
                              'Approved account successfully - ' + usr.username)

                    usr.is_active = True
                    usr.save()
                else:
                    logger.info(f'User {usr.username} was already active')
            else:
                logger.info(f'There is no User record with the ID: {pu.user_id}')

    def get_actions(self, request):
        actions = super(PendingAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['activate_users']
        return actions


class DomainWhitelistAdmin(CompareVersionAdmin):
    list_display = ('domain_name', 'description', 'is_active')
    search_fields = ('domain_name',)
    ordering = ('domain_name',)


admin.site.register(models.Pending, PendingAdmin)
admin.site.register(models.DomainWhitelist, DomainWhitelistAdmin)
