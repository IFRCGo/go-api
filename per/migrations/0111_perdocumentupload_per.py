# Generated by Django 3.2.25 on 2024-04-02 05:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0110_auto_20240325_0611"),
    ]

    operations = [
        migrations.AddField(
            model_name="perdocumentupload",
            name="per",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="per.overview", verbose_name="Per"
            ),
        ),
    ]
