# Generated by Django 3.2.24 on 2024-03-14 10:59

from django.db import migrations


def update_component_question_group(apps, schema_editor):
    FormComponent = apps.get_model("per", "FormComponent")
    FormComponent.objects.filter(id=48, formcomponentresponse__rating__isnull=True).update(has_question_group=True)


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0105_formcomponent_has_question_group"),
    ]

    operations = [
        migrations.RunPython(update_component_question_group, reverse_code=migrations.RunPython.noop),
    ]
