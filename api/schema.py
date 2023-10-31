import graphene
from graphene_django.types import DjangoObjectType
from .models import (
    Country,
    DisasterType,
    ActionsTaken,
    Event,
    Appeal,
    FieldReport,
)


# GraphQL Schemas
class CountryObjectType(DjangoObjectType):
    class Meta:
        model = Country


class DisasterObjectType(DjangoObjectType):
    class Meta:
        model = DisasterType


class EventType(DjangoObjectType):
    class Meta:
        model = Event


class ActionsTakenType(DjangoObjectType):
    class Meta:
        model = ActionsTaken


class AppealType(DjangoObjectType):
    class Meta:
        model = Appeal


class FieldReportType(DjangoObjectType):
    class Meta:
        model = FieldReport


class Query(graphene.ObjectType):
    all_countries = graphene.List(CountryObjectType)
    all_disasters_types = graphene.List(DisasterObjectType)
    all_events = graphene.List(EventType)
    all_events = graphene.List(EventType)
    all_appeals = graphene.List(AppealType)
    all_fieldreports = graphene.List(FieldReportType)

    def resolve_all_disasters(self, info, **kwargs):
        return DisasterType.objects.all()

    def resolve_all_events(self, info, **kwargs):
        return Event.objects.select_related('dtype').all()

    def resolve_all_appeals(self, info, **kwargs):
        return Appeal.objects.select_related('event').select_related('country').all()

    def resolve_all_fieldreports(self, info, **kwargs):
        return FieldReport.objects.select_related('dtype').select_related('event').all()


schema = graphene.Schema(query=Query)
