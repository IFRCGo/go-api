# Generated by Django 4.2.15 on 2024-09-18 04:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0001_squashed_0120_alter_formcomponent_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="overview",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="perworkplancomponent",
            name="component",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="per.formcomponent", verbose_name="Component"
            ),
        ),
    ]
