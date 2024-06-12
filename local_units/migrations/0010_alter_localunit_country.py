# Generated by Django 3.2.25 on 2024-05-06 06:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0210_profile_accepted_montandon_license_terms"),
        ("local_units", "0009_alter_localunit_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="localunit",
            name="country",
            field=models.ForeignKey(
                default=14,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="local_unit_country",
                to="api.country",
                verbose_name="Country",
            ),
            preserve_default=False,
        ),
    ]
