from functools import reduce
from operator import or_

from django.contrib import admin
from django.db.models import Q
from django.http import QueryDict
from django.shortcuts import redirect


class RegionRestrictedAdmin(admin.ModelAdmin):
    """
    Extend the model admin with methods for determining whether a user has
    country- and region-specific permissions.
    If the user does not have specific permissions for any country or region,
    the result is an empty queryset.
    """

    def get_request_user_regions(self, request):
        permissions = request.user.get_all_permissions()
        regions = []
        countries = []
        for permission_name in permissions:
            if "api.per_country_admin_" in permission_name:
                country_id = permission_name[22:]
                if country_id.isdigit():
                    countries.append(country_id)
            elif "api.per_region_admin_" in permission_name:
                region_id = permission_name[21:]
                if region_id.isdigit():
                    regions.append(region_id)
        return countries, regions

    def get_filtered_queryset(self, request, queryset, dispatch):
        if request.user.is_superuser or request.user.has_perm("api.per_core_admin"):
            return queryset
        countries, regions = self.get_request_user_regions(request)

        if not len(countries) and not len(regions):
            return queryset.none()

        # if dispatch == 0:
        #     # Admin classes
        #     country_in = getattr(self, "country", None)
        #     region_in = getattr(self, "region", None)
        # elif dispatch == 1:
        #     # Form
        #     country_in = "overview__country_id__in"
        #     region_in = "overview__country__region_id__in"
        # elif dispatch == 2:
        #     # FormData
        #     country_in = "form__overview__country_id__in"
        #     region_in = "form__overview__country__region_id__in"
        # elif dispatch == 3:
        #     # Country
        #     country_in = "pk__in"
        #     region_in = "region_id__in"
        # elif dispatch == 4:
        #     # NiceDocuments, PERDocsViewset
        #     country_in = "country_id__in"
        #     region_in = "country__region__in"

        # Create a list to store Q objects
        queries = []

        # Check for conditions and add them to the list
        if countries:
            queries.append(Q(country__in=countries))
        if regions:
            queries.append(Q(country__region__in=regions))

        # Use reduce and the or_ operator to combine the Q objects
        if queries:
            combined_query = reduce(or_, queries)
            return queryset.filter(combined_query).distinct()
        else:
            return queryset.none()

    # Gets called by default from the Admin classes
    def get_queryset(self, request):
        queryset = super(admin.ModelAdmin, self).get_queryset(request)
        return self.get_filtered_queryset(request, queryset, 0)


class GotoNextModelAdmin(admin.ModelAdmin):

    def get_next_instance_pk(self, request, current):
        """
        Source: stackoverflow.com/questions/58014139/how-to-go-to-next-object-in-django-admin
        Returns the primary key of the next object in the query (considering filters and ordering).
        Returns None if the object is not in the queryset.
        """
        querystring = request.GET.get("_changelist_filters")
        if querystring:
            # Alters the HttpRequest object to make it function as a list request
            original_get = request.GET
            try:
                request.GET = QueryDict(querystring)
                # from django.contrib.admin.options: ModelAdmin.changelist_view
                ChangeList = self.get_changelist(request)
                list_display = self.get_list_display(request)
                changelist = ChangeList(
                    request,
                    self.model,
                    list_display,
                    self.get_list_display_links(request, list_display),
                    self.get_list_filter(request),
                    self.date_hierarchy,
                    self.get_search_fields(request),
                    self.get_list_select_related(request),
                    self.list_per_page,
                    self.list_max_show_all,
                    self.list_editable,
                    self,
                    self.sortable_by,
                )  # New in Django 2.0
                queryset = changelist.get_queryset(request)
            finally:
                request.GET = original_get
        else:
            queryset = self.get_queryset(request)

        # Try to find pk in this list:
        iterator = queryset.values_list("pk", flat=True).iterator()
        try:
            while next(iterator) != current.pk:
                continue
            return next(iterator)
        except StopIteration:
            pass  # Not found or it was the last item

    def response_change(self, request, obj):
        """Determines the HttpResponse for the change_view stage."""
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        if "_save_next" in request.POST:
            next_pk = self.get_next_instance_pk(request, obj)
            if next_pk:
                response = redirect(f"admin:{app_label}_{model_name}_change", next_pk)
                qs = request.GET.urlencode()  # keeps _changelist_filters
            else:
                # Last item (or no longer in list) - go back to list in the same position
                response = redirect(f"admin:{app_label}_{model_name}_changelist")
                qs = request.GET.get("_changelist_filters")
            if qs:
                response["Location"] += "?" + qs
            return response
        return super().response_change(request, obj)

    # stackoverflow.com/questions/49560378/cannot-hide-save-and-add-another-button-in-django-admin
    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context.update({"show_save_and_next": True})
        return super().render_change_form(request, context, add, change, form_url, obj)
