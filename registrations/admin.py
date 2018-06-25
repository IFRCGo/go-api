from django.contrib import admin
import registrations.models as models


class PendingAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'admin_contact_1', 'admin_contact_2')


admin.site.register(models.Pending, PendingAdmin)
