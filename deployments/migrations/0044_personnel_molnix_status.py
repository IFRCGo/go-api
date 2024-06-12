# Generated by Django 2.2.27 on 2022-03-10 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0043_personnel_country_to_fill"),
    ]

    operations = [
        migrations.AddField(
            model_name="personnel",
            name="molnix_status",
            field=models.CharField(
                choices=[("active", "ACTIVE"), ("hidden", "HIDDEN"), ("draft", "DRAFT"), ("deleted", "DELETED")],
                default="active",
                max_length=8,
                verbose_name="molnix status",
            ),
        ),
    ]
