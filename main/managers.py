import abc
import typing
from collections import defaultdict

from django.apps import apps
from django.db import models


class BaseBulkManager(object):
    """
    This helper class keeps track of ORM objects to be action for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is action for all models.
    """

    def __init__(self, chunk_size: int = 100):
        self._queues = defaultdict(list)
        self.chunk_size = chunk_size
        self._summary = defaultdict(int)

    @abc.abstractmethod
    def _commit(self, model_class: typing.Type[models.Model]):
        raise NotImplementedError

    def _process_obj(self, obj: models.Model):
        return obj

    def add(self, *objs: models.Model):
        """
        Add an object to the queue to be action, and call bulk_create if we
        have enough objs.
        """
        for obj in objs:
            model_class = type(obj)
            model_key = model_class._meta.label
            self._queues[model_key].append(self._process_obj(obj))
            if len(self._queues[model_key]) >= self.chunk_size:
                self._commit(model_class)

    def done(self):
        """
        Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))

    @abc.abstractmethod
    def summary(self):
        raise NotImplementedError


class BulkCreateManager(BaseBulkManager):
    def _commit(self, model_class: typing.Type[models.Model]):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._queues[model_key])
        self._summary[model_key] += len(self._queues[model_key])
        self._queues[model_key] = []

    @abc.abstractmethod
    def summary(self):
        return {"added": dict(self._summary)}


class BulkUpdateManager(BaseBulkManager):
    def __init__(self, update_fields: typing.List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_fields = update_fields

    def _process_obj(self, obj: models.Model):
        if obj.pk is None:
            raise Exception(f"Only object with pk is allowed: {obj}")
        return obj

    def _commit(self, model_class: typing.Type[models.Model]):
        model_key = model_class._meta.label
        model_class.objects.bulk_update(self._queues[model_key], self.update_fields)
        self._summary[model_key] += len(self._queues[model_key])
        self._queues[model_key] = []

    @abc.abstractmethod
    def summary(self):
        return {"updated": dict(self._summary)}
