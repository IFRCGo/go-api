from django.contrib import admin
from django.db.models import Q

# Extend the model admin with methods for determining whether a user has
# country- and region-specific permissions.
# If the user does not have specific permissions for any country or region,
# the result is an empty queryset.

class RegionRestrictedAdmin(admin.ModelAdmin):
    def get_request_user_regions(self, request):
        permissions = request.user.get_all_permissions()
        regions = []
        countries = []
        for permission_name in permissions:
            if 'api.per_country_admin_' in permission_name:
                country_id = permission_name[22:]
                if country_id.isdigit():
                    countries.append(country_id)
            elif 'api.per_region_admin_' in permission_name:
                region_id = permission_name[21:]
                if region_id.isdigit():
                    regions.append(region_id)
        return countries, regions

    def get_filtered_queryset(self, request, queryset, dispatch):
        if request.user.is_superuser or request.user.has_perm('api.ifrc_admin') or request.user.has_perm('api.per_core_admin'):
            return queryset
        countries, regions = self.get_request_user_regions(request)

        # No countries and regions are present;
        # return an empty queryset
        if not len(countries) and not len(regions):
            return queryset.none()

        if dispatch == 0: # Django admin filtering
        # Create an OR filter for records relating to this country or region
            country_in = getattr(self, 'country_in', None)
            region_in = getattr(self, 'region_in', None)
        elif dispatch == 1:
        # From drf_views.py - collection of PER-user-relevant PER form headers
            from .admin import FormAdmin
            country_in = FormAdmin.country_in
            region_in = FormAdmin.region_in
        elif dispatch == 2:
        # From drf_views.py - collection of PER-user-relevant PER data
            from .admin import FormDataAdmin
            country_in = FormDataAdmin.country_in
            region_in = FormDataAdmin.region_in
        elif dispatch == 3:
        # From drf_views.py - collection of PER-user-relevant countries
            country_in = 'pk__in'
            region_in = 'region_id__in'
        elif dispatch == 4:
        # From drf_views.py NiceDocuments, PERDocsViewset - collection of PER-user-relevant countries for Docs
            country_in = 'country_id__in'
            region_in = 'country__region__in'

        query = Q()
        has_valid_query = False
        if len(countries) and country_in is not None:
            query.add(Q(**{country_in: countries}), Q.OR)
            has_valid_query = True
        if len(regions) and region_in is not None:
            query.add(Q(**{region_in: regions}), Q.OR)
            has_valid_query = True
        return queryset.filter(query) if has_valid_query else queryset.none()

    def get_queryset(self, request):
        queryset = super(admin.ModelAdmin, self).get_queryset(request)
        return self.get_filtered_queryset(request, queryset, 0)
