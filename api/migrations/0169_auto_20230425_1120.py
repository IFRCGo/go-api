# Generated by Django 3.2.18 on 2023-04-25 11:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0168_alter_country_iso"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appealdocument",
            name="iso3",
        ),
        migrations.AddField(
            model_name="appealdocument",
            name="iso",
            field=models.ForeignKey(
                db_column="iso",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.country",
                to_field="iso",
                verbose_name="location",
            ),
        ),
    ]
