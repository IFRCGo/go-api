# from datetime import datetime, timedelta, timezone
# from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.widgets import CSVWidget
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from deployments.models import MolnixTag
from main.filters import CharInFilter
from main.permissions import DenyGuestUserPermission

from .models import Subscription, SurgeAlert
from .serializers import (  # UnauthenticatedSurgeAlertSerializer,
    SubscriptionSerializer,
    SurgeAlertSerializer,
)


class SurgeAlertFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name="atype", lookup_expr="exact")
    category = filters.NumberFilter(field_name="category", lookup_expr="exact")
    event = filters.NumberFilter(field_name="event", lookup_expr="exact")
    molnix_tags = filters.ModelMultipleChoiceFilter(
        label="tag-ids",
        field_name="molnix_tags",
        help_text="Molnix_tag GO identifiers, comma separated",
        widget=CSVWidget,
        queryset=MolnixTag.objects.all(),
    )
    molnix_tag_name = filters.CharFilter(
        field_name="molnix_tags__name",
        lookup_expr="icontains",
        label="tag-name",
        help_text="Single partial match on Molnix tag name",
    )
    molnix_tag_names = CharInFilter(
        label="tag-names",
        field_name="molnix_tags__name",
        lookup_expr="in",
        help_text="Molnix_tag names, comma separated",
        widget=CSVWidget,
    )
    molnix_status = CharInFilter(
        label="molnix status",
        field_name="molnix_status",
        lookup_expr="in",
        help_text="Molnix status value, comma separated",
        widget=CSVWidget,
    )

    class Meta:
        model = SurgeAlert
        fields = {
            "created_at": ("exact", "gt", "gte", "lt", "lte"),
            "start": ("exact", "gt", "gte", "lt", "lte"),
            "end": ("exact", "gt", "gte", "lt", "lte"),
            "molnix_id": ("exact", "in"),
            "message": ("exact", "in", "icontains"),
            "country": ("exact", "in"),
            "country__name": ("exact", "in", "icontains"),
            "country__iso": ("exact", "in"),
            "country__iso3": ("exact", "in"),
        }

    @property
    def qs(self):
        return super().qs.distinct()


class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    queryset = SurgeAlert.objects.prefetch_related("molnix_tags", "molnix_tags__groups").select_related("event", "country").all()
    filterset_class = SurgeAlertFilter
    ordering_fields = ("created_at", "atype", "category", "event", "molnix_status", "opens")
    search_fields = (
        "operation",
        "message",
        "event__name",
    )  # for /docs

    def get_serializer_class(self):
        # if self.request.user.is_authenticated:
        #     return SurgeAlertSerializer
        # return UnauthenticatedSurgeAlertSerializer
        return SurgeAlertSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(molnix_id__isnull=False).exclude(molnix_tags__name="NO_GO")


#   def get_queryset(self):
#       # limit = 14  # days
#       # cond1 = Q(is_stood_down=True)
#       # cond2 = Q(end__lt=datetime.utcnow().replace(tzinfo=timezone.utc)-timedelta(days=limit))
#       return super().get_queryset()
#       #    exclude(cond1 & cond2)


class SubscriptionViewset(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, DenyGuestUserPermission)
    search_fields = ("user__username", "rtype")  # for /docs

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
