from rest_framework import mixins, viewsets
from django.db import models

from .models import CountryPlan, MembershipCoordination
from .serializers import CountryPlanSerializer


class CountryPlanViewset(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CountryPlanSerializer
    queryset = CountryPlan.objects.prefetch_related(
        'country_plan_sp',
        models.Prefetch(
            'country_plan_mc',
            queryset=MembershipCoordination.objects.annotate(
                national_society_name=models.F('national_society__society_name'),
            ),
        ),
    ).filter(is_publish=True)
