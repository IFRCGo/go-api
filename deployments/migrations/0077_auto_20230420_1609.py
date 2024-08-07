# Generated by Django 3.2.18 on 2023-04-20 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0164_appealdocumenttype"),
        ("deployments", "0076_auto_20230309_1556"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emergencyproject",
            name="districts",
            field=models.ManyToManyField(
                blank=True, related_name="_deployments_emergencyproject_districts_+", to="api.District", verbose_name="Districts"
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="project_districts",
            field=models.ManyToManyField(blank=True, to="api.District", verbose_name="districts"),
        ),
    ]
