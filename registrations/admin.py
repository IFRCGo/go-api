from django.contrib import admin
import registrations.models as models
from reversion_compare.admin import CompareVersionAdmin


class PendingAdmin(CompareVersionAdmin):
    search_fields = ('user__username', 'user__email', 'admin_contact_1', 'admin_contact_2')
    list_display = ('get_username_and_mail', 'created_at',
                    'admin_contact_1', 'admin_1_validated', 'admin_1_validated_date',
                    'admin_contact_2', 'admin_2_validated', 'admin_2_validated_date', 'email_verified',)

    def get_username_and_mail(self, obj):
        return obj.user.username + ' - ' + obj.user.email


class DomainWhitelistAdmin(CompareVersionAdmin):
    list_display = ('domain_name', 'description', 'is_active')
    search_fields = ('domain_name',)
    ordering = ('domain_name',)


admin.site.register(models.Pending, PendingAdmin)
admin.site.register(models.DomainWhitelist, DomainWhitelistAdmin)
