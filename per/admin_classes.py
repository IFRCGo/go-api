from functools import reduce
from operator import or_

from django.contrib import admin
from django.db.models import Q


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
