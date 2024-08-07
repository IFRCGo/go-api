# Generated by Django 3.2.23 on 2024-02-22 05:45
from django.db import migrations, models


# NOTE: Same as 0099_migrate_notes but this migrates all of the notes using Question "Component performance"
# For more info look at per/migrations/0086_migrate_old_form.py
def migrate_formdata_notes(apps, schema_editor):
    FormComponentResponse = apps.get_model("per", "FormComponentResponse")
    FormData = apps.get_model("per", "FormData")

    qs = FormComponentResponse.objects.annotate(
        new_notes=models.Subquery(
            # Copy notes from FormData using overview
            FormData.objects.filter(
                form__overview=models.OuterRef("arearesponse__perassessment__overview"),
                question__component=models.OuterRef("component"),
                question__question__iexact="Component performance",
            ).values("notes_en"),
            output_field=models.CharField(),
        ),
    ).filter(new_notes__isnull=False)

    form_component_responses = []
    for form_component_response_id, assessment_id, new_notes in qs.values_list(
        "id",
        models.F("arearesponse__perassessment"),
        "new_notes",
    ):
        print(f"- Copying data for {assessment_id=} {form_component_response_id=}")
        form_component_responses.append(
            FormComponentResponse(
                id=form_component_response_id,
                notes=new_notes,
            )
        )

    print(f"Total form_component_responses notes copied: {len(form_component_responses)}")
    FormComponentResponse.objects.bulk_update(form_component_responses, fields=("notes",))


class Migration(migrations.Migration):
    dependencies = [
        ("per", "0099_migrate_notes"),
    ]

    operations = [
        migrations.RunPython(migrate_formdata_notes, reverse_code=migrations.RunPython.noop),
    ]
