# Generated by Django 3.2.23 on 2024-02-22 05:45
from django.db import migrations
from django.db import models

from api.logger import logger


class Migration(migrations.Migration):
    def migrate_formdata_notes(apps, schema_editor):
        # NOTE: No any exact match for relationships
        FormComponentResponse = apps.get_model("per", "FormComponentResponse")
        FormData = apps.get_model("per", "FormData")
        qs = FormComponentResponse.objects.annotate(
            new_notes=models.Subquery(
                FormData.objects.filter(
                    question__component=models.OuterRef("component"),
                    question=74,
                )
                .order_by(
                    "-form__area",
                    "-form__created_at",
                    "form",
                    "question__question_num",
                )
                .filter(notes__isnull=False)
                .values("notes_en")[:1],
                output_field=models.CharField(),
            ),
        ).filter(new_notes__isnull=False)

        print(
            qs.update(
                notes=models.F("new_notes"),
            )
        )

    dependencies = [
        ("per", "0098_fix_reversion_data_20240208_0502"),
    ]

    operations = [
        migrations.RunPython(migrate_formdata_notes, reverse_code=migrations.RunPython.noop),
    ]
