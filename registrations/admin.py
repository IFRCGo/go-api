from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from reversion_compare.admin import CompareVersionAdmin

import registrations.models as models
from api.logger import logger
from api.models import Country, Profile, User, UserRegion
from notifications.notification import send_notification


class PendingAdmin(CompareVersionAdmin):
    readonly_fields = (
        "get_username_and_mail",
        "get_region",
        "get_country",
        "get_org",
        "get_city",
        "get_department",
        "get_position",
        "get_phone",
        "justification",
        "created_at",
        "email_verified",
    )
    search_fields = ("user__username", "user__email", "admin_contact_1", "admin_contact_2")
    list_display = ("get_username_and_mail", "get_region", "get_country", "created_at", "email_verified")
    actions = ("activate_users",)
    list_filter = (
        "email_verified",
        ("user__profile__country__region", RelatedDropdownFilter),
        ("user__profile__country", RelatedDropdownFilter),
    )

    change_form_template = "admin/pending_change_form.html"
    change_list_template = "admin/pending_change_list.html"

    # Get the 'user' objects with a JOIN query
    def get_queryset(self, request):
        if request.user.is_superuser:
            retval = super().get_queryset(request).select_related("user").exclude(user__is_active=1)
        else:
            region_id = UserRegion.objects.filter(user_id=request.user.id).values_list("region_id", flat=True)
            country_ids = Country.objects.filter(region_id__in=region_id).values_list("id", flat=True)
            user_ids = Profile.objects.filter(country_id__in=country_ids).values_list("user_id", flat=True)

            retval = super().get_queryset(request).select_related("user").filter(user_id__in=user_ids).exclude(user__is_active=1)

        return retval

    def get_username_and_mail(self, obj):
        return obj.user.username + " - " + obj.user.email

    get_username_and_mail.short_description = "Username - Email"
    get_username_and_mail.admin_order_field = "user__username"

    def get_region(self, obj):
        if obj.user.profile.country:
            return obj.user.profile.country.region
        else:
            return obj.user.profile.country

    get_region.short_description = "Region"
    get_region.admin_order_field = "user__profile__country__region"

    def get_country(self, obj):
        return obj.user.profile.country

    get_country.short_description = "Country"
    get_country.admin_order_field = "user__profile__country"

    def get_org(self, obj):
        return obj.user.profile.organization

    get_org.short_description = "Organization"
    get_org.admin_order_field = "user__profile__organization"

    def get_city(self, obj):
        return obj.user.profile.city

    get_city.short_description = "City"
    get_city.admin_order_field = "user__profile__city"

    def get_department(self, obj):
        return obj.user.profile.department

    get_department.short_description = "Department"
    get_department.admin_order_field = "user__profile__department"

    def get_position(self, obj):
        return obj.user.profile.position

    get_position.short_description = "Position"
    get_position.admin_order_field = "user__profile__position"

    def get_phone(self, obj):
        return obj.user.profile.phone

    get_phone.short_description = "Phone"
    get_phone.admin_order_field = "user__profile__phone"

    def user_is_active(self, obj):
        return "Yes" if obj.user.is_active else ""

    def activate_users(self, request, queryset):
        for pu in queryset:
            usr = User.objects.filter(id=pu.user_id).first()
            if usr:
                if usr.is_active is False:

                    email_context = {"frontend_url": settings.GO_WEB_URL}

                    send_notification(
                        "Your account has been approved",
                        [usr.email],
                        render_to_string("email/registration/outside-email-success.html", email_context),
                        f"Approved account successfully - {usr.username}",
                    )

                    usr.is_active = True
                    usr.save()
                else:
                    logger.info(f"User {usr.username} was already active")
            else:
                logger.info(f"There is no User record with the ID: {pu.user_id}")

    def response_change(self, request, obj):
        if "_activate-user" in request.POST:
            usr = User.objects.get(id=obj.user.id)

            if usr:
                if usr.is_active is False:

                    email_context = {"frontend_url": settings.GO_WEB_URL}

                    send_notification(
                        "Your account has been approved",
                        [usr.email],
                        render_to_string("email/registration/outside-email-success.html", email_context),
                        f"Approved account successfully - {usr.username}",
                    )

                    usr.is_active = True
                    usr.save()
                else:
                    logger.info(f"User {usr.username} was already active")
            else:
                logger.info(f"There is no User record with the ID: {obj.user.id}")

            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = {
            "show_approve_user": True,
            "show_save": False,
            "show_save_and_add_another": False,
            "show_save_and_continue": False,
        }
        return self.changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if "_approve_user" in request.POST:
            self.activate_users(request, [obj])
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super(PendingAdmin, self).get_actions(request)
        return actions


class DomainWhitelistAdmin(CompareVersionAdmin):
    list_display = ("domain_name", "description", "is_active")
    search_fields = ("domain_name",)
    ordering = ("domain_name",)


# NOTE: External systems (eg. Montandon eoAPI) cache the revocation list, so re-enabling a
# disabled token is not applied instantly downstream.
RE_ENABLE_PROPAGATION_HINT = (
    "Re-enabling a disabled token may take some time to take effect: "
    "external systems (eg. Montandon eoAPI) can keep it in their revoke list until their cache expires."
)


class UserExternalTokenAdminForm(forms.ModelForm):
    class Meta:
        model = models.UserExternalToken
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "is_disabled" in self.fields:
            self.fields["is_disabled"].help_text = RE_ENABLE_PROPAGATION_HINT


class UserExternalTokenAdmin(CompareVersionAdmin):
    form = UserExternalTokenAdminForm
    list_display = ("title", "user", "created_at", "expire_timestamp", "is_disabled", "is_old_token")
    list_filter = ("is_disabled", "is_old_token")
    search_fields = ("title", "user__username", "user__email", "jti")
    readonly_fields = ("jti", "created_at")
    autocomplete_fields = ("user",)
    actions = ("disable_tokens", "enable_tokens")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is not None:
            # Expiry is fixed at creation time and is baked into the already issued JWT
            return readonly_fields + ("expire_timestamp",)
        return readonly_fields

    @admin.action(description="Disable selected tokens")
    def disable_tokens(self, request, queryset):
        updated = queryset.update(is_disabled=True)
        self.message_user(request, f"{updated} token(s) disabled.")

    @admin.action(description="Enable selected tokens")
    def enable_tokens(self, request, queryset):
        updated = queryset.update(is_disabled=False)
        self.message_user(request, f"{updated} token(s) enabled. {RE_ENABLE_PROPAGATION_HINT}", messages.WARNING)


admin.site.register(models.Pending, PendingAdmin)
admin.site.register(models.DomainWhitelist, DomainWhitelistAdmin)
admin.site.register(models.UserExternalToken, UserExternalTokenAdmin)
