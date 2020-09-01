from django.contrib import admin
from api.models import User
import registrations.models as models
from reversion_compare.admin import CompareVersionAdmin


class PendingAdmin(CompareVersionAdmin):
    search_fields = ('user__username', 'user__email', 'admin_contact_1', 'admin_contact_2')
    list_display = (
        'get_username_and_mail', 'created_at',
        'admin_contact_1', 'admin_1_validated', 'admin_1_validated_date',
        'admin_contact_2', 'admin_2_validated', 'admin_2_validated_date',
        'email_verified'
    )
    actions = ('activate_users',)

    def get_username_and_mail(self, obj):
        return obj.user.username + ' - ' + obj.user.email

    def activate_users(self, request, queryset):
        for pu in queryset:
            usr = User.objects.filter(id=pu.user_id).first()
            if usr:
                usr.is_active = True
                usr.save()

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
