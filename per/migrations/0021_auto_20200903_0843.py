# Generated by Django 2.2.13 on 2020-09-03 08:43

from django.db import migrations, models

import per.models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0020_auto_20200618_0904"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nicedocument",
            name="document",
            field=models.FileField(blank=True, null=True, upload_to=per.models.nice_document_path, verbose_name="document"),
        ),
    ]
