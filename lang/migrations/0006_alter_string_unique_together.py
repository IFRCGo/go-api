# Generated by Django 3.2.20 on 2023-10-16 07:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lang", "0005_string_page_name"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="string",
            unique_together={("language", "page_name", "key")},
        ),
    ]
