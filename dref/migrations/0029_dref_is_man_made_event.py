# Generated by Django 2.2.27 on 2022-08-18 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0028_auto_20220817_1013"),
    ]

    operations = [
        migrations.AddField(
            model_name="dref",
            name="is_man_made_event",
            field=models.BooleanField(default=False, verbose_name="Is Man-made Event"),
        ),
    ]
