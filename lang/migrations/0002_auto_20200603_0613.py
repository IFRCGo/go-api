# Generated by Django 2.2.10 on 2020-06-03 06:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lang", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="language",
            options={"verbose_name": "Language", "verbose_name_plural": "Languages"},
        ),
        migrations.AlterModelOptions(
            name="string",
            options={"verbose_name": "String", "verbose_name_plural": "Strings"},
        ),
    ]
