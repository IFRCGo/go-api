# Generated by Django 3.2.19 on 2023-06-19 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0060_dreffinalreport_date_of_approval"),
    ]

    operations = [
        migrations.AddField(
            model_name="dref",
            name="is_active",
            field=models.BooleanField(blank=True, null=True, verbose_name="Is Active"),
        ),
    ]
