# Generated by Django 2.2.24 on 2021-12-27 14:41

from django.db import migrations, models

import api.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0136_event_visibility"),
    ]

    operations = [
        migrations.AlterField(
            model_name="generaldocument",
            name="document",
            field=models.FileField(blank=True, null=True, upload_to=api.models.general_document_path, verbose_name="document"),
        ),
        migrations.AlterField(
            model_name="generaldocument",
            name="name_ar",
            field=models.CharField(max_length=100, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="generaldocument",
            name="name_en",
            field=models.CharField(max_length=100, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="generaldocument",
            name="name_es",
            field=models.CharField(max_length=100, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="generaldocument",
            name="name_fr",
            field=models.CharField(max_length=100, null=True, verbose_name="name"),
        ),
    ]
