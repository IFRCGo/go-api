import factory

from alert_system.models import AlertEmailLog, AlertEmailThread, Connector, LoadItem


class LoadItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoadItem

    @factory.post_generation
    def related_montandon_events(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for event in extracted:
                self.related_montandon_events.add(event)

    @factory.post_generation
    def related_go_events(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for event in extracted:
                self.related_go_events.add(event)


class AlertEmailLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AlertEmailLog


class ConnectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Connector


class AlertEmailThreadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AlertEmailThread
