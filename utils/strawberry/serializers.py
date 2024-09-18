from django.db import models
from rest_framework import serializers


class IntegerIDField(serializers.IntegerField):
    """
    This field is created to override the graphene conversion of the integerfield -> graphene.ID
    check out utils/graphene/mutation.py
    """

    pass


class StringIDField(serializers.CharField):
    """
    This field is created to override the graphene conversion of the charField -> graphene.ID
    check out utils/graphene/mutation.py
    """

    pass


class CustomCharField(serializers.CharField):
    """
    This is match utils/strawberry/types.py::string_field logic
    """

    def run_validation(self, data=serializers.empty):
        if data is None and self.allow_blank and not self.allow_null:
            data = ""
        return super().run_validation(data)


class TimeDurationField(serializers.IntegerField):
    """
    This field is created to override the graphene conversion of the integerfield -> TimeDurationField
    """

    pass


serializers.ModelSerializer.serializer_field_mapping.update(
    {
        models.CharField: CustomCharField,
        models.TextField: CustomCharField,
    }
)
