from rest_framework import serializers

from dref import enums as dref_enums
from api import enums as api_enums
from flash_update import enums as flash_update_enums
from deployments import enums as deployments_enums
from per import enums as per_enums


apps_enum_register = [
    ('dref', dref_enums.enum_register),
    ('api', api_enums.enum_register),
    ('flash_update', flash_update_enums.enum_register),
    ('deployments', deployments_enums.enum_register),
    ('per', per_enums.enum_register),
]


def underscore_to_camel(text):
    return text.replace('_', ' ').title().replace(' ', '')


def generate_global_enum_register():
    enum_map = {}
    enum_names = set()
    for app_prefix, app_enum_register in apps_enum_register:
        for enum_field, enum in app_enum_register.items():
            # Change field dref_national_society_action_title -> DrefNationalSocietyActionTitle
            _enum_field = f'{app_prefix}_{enum_field}'
            enum_name = f'{underscore_to_camel(_enum_field)}EnumSerializer'
            if enum_name in enum_names:
                raise Exception(f'Duplicate enum_names found for {enum_name} in {enum_names}')
            enum_names.add(enum_name)
            enum_map[_enum_field] = (enum_name, enum)
    return enum_map


global_enum_registers = generate_global_enum_register()


def generate_enum_global_serializer(name):
    def _get_enum_key_value_serializer(enum, enum_name):
        return type(
            enum_name,
            (serializers.Serializer,),
            {
                'key': serializers.ChoiceField(enum.choices),
                'value': serializers.CharField(),
            },
        )

    fields = {}
    for enum_field, (enum_name, enum) in global_enum_registers.items():
        fields[enum_field] = _get_enum_key_value_serializer(enum, enum_name)(many=True, required=False)
    return type(name, (serializers.Serializer,), fields)


GlobalEnumSerializer = generate_enum_global_serializer('GlobalEnumSerializer')


def get_enum_values():
    enum_data = {
        enum_field: [
            {
                'key': key,
                'value': value,
            }
            for key, value in enum.choices
        ]
        for enum_field, (_, enum) in global_enum_registers.items()
    }
    return GlobalEnumSerializer(enum_data).data
