# Generated by Django 2.2.27 on 2022-03-11 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0049_auto_20220311_0400"),
    ]

    operations = [
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="people_households",
            field=models.CharField(
                blank=True,
                choices=[("people", "People"), ("households", "Households")],
                max_length=50,
                null=True,
                verbose_name="People Households",
            ),
        ),
    ]
