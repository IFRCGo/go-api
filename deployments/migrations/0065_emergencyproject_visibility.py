# Generated by Django 2.2.27 on 2022-04-27 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0064_auto_20220414_0842"),
    ]

    operations = [
        migrations.AddField(
            model_name="emergencyproject",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("logged_in_user", "Membership"),
                    ("ifrc_only", "IFRC Only"),
                    ("public", "Public"),
                    ("ifrc_ns", "IFRC_NS"),
                ],
                default="public",
                max_length=32,
                verbose_name="visibility",
            ),
        ),
    ]
