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
