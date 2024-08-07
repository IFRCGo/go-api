# Generated by Django 4.2.13 on 2024-05-19 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0210_profile_accepted_montandon_license_terms"),
        ("deployments", "0088_alter_project_visibility"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emergencyproject",
            name="districts",
            field=models.ManyToManyField(blank=True, related_name="+", to="api.district", verbose_name="Districts"),
        ),
    ]
