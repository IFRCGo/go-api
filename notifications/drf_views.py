# from datetime import datetime, timedelta, timezone
# from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.widgets import CSVWidget
from main.filters import CharInFilter
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import SurgeAlert, Subscription
from deployments.models import MolnixTag
from .serializers import (
    SurgeAlertSerializer,
    # UnauthenticatedSurgeAlertSerializer,
    SubscriptionSerializer,
)


class SurgeAlertFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name='atype', lookup_expr='exact')
    category = filters.NumberFilter(field_name='category', lookup_expr='exact')
    event = filters.NumberFilter(field_name='event', lookup_expr='exact')
    molnix_tags = filters.ModelMultipleChoiceFilter(
        label='tag-ids',
        field_name='molnix_tags',
        help_text='Molnix_tag GO identifiers, comma separated',
        widget=CSVWidget,
        queryset=MolnixTag.objects.all(),
    )
    molnix_tag_names = CharInFilter(
        label='tag-names',
        field_name='molnix_tags__name',
        lookup_expr='in',
        help_text='Molnix_tag names, comma separated',
        widget=CSVWidget,
    )

    class Meta:
        model = SurgeAlert
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'start': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'end': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'is_stood_down': ('exact',),
            'is_active': ('exact',),
            'molnix_id': ('exact', 'in'),
            'molnix_status': ('exact', 'in'),
            'message': ('exact', 'in'),
            'country': ('exact', 'in'),
            'country__name': ('exact', 'in'),
            'country__iso': ('exact', 'in'),
            'country__iso3': ('exact', 'in'),
        }

    @property
    def qs(self):
        return super().qs.distinct()


class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    queryset = SurgeAlert.objects.all()
    filterset_class = SurgeAlertFilter
    ordering_fields = ('created_at', 'atype', 'category', 'event', 'is_stood_down',)
    search_fields = ('operation', 'message', 'event__name',)  # for /docs

    def get_serializer_class(self):
        # if self.request.user.is_authenticated:
        #     return SurgeAlertSerializer
        # return UnauthenticatedSurgeAlertSerializer
        return SurgeAlertSerializer

    def get_queryset(self):
        # limit = 14  # days
        # cond1 = Q(is_stood_down=True)
        # cond2 = Q(end__lt=datetime.utcnow().replace(tzinfo=timezone.utc)-timedelta(days=limit))
        return super().get_queryset().\
            select_related('country')
        #    exclude(cond1 & cond2)  # 'event' inclusion ^ to _related needs frontend change, otherwise the Position column shows garbage in /alerts/all


class SubscriptionViewset(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    search_fields = ('user__username', 'rtype')  # for /docs

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
