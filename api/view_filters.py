from django.db.models import Q
from django_filters import Filter


# https://github.com/carltongibson/django-filter/issues/137#issuecomment-127073878
class ListFilter(Filter):
    def __init__(self, filter_value=lambda x: x, **kwargs):
        super(ListFilter, self).__init__(**kwargs)
        self.filter_value_fn = filter_value

    def sanitize(self, value_list):
        return [v for v in value_list if v != u'']

    def filter(self, qs, value):
        values = value.split(u",") if value is not None else []
        values = self.sanitize(values)
        values = map(self.filter_value_fn, values)
        f = Q()
        for v in values:
            kwargs = {self.field_name: v}
            f = f | Q(**kwargs)
        return qs.filter(f)
