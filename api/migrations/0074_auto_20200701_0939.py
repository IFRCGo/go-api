# Generated by Django 2.2.13 on 2020-07-01 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0073_auto_20200624_1538"),
    ]

    operations = [
        migrations.AlterField(
            model_name="countrysnippet",
            name="snippet",
            field=models.TextField(blank=True, null=True, verbose_name="snippet"),
        ),
        migrations.AlterField(
            model_name="regionsnippet",
            name="snippet",
            field=models.TextField(blank=True, null=True, verbose_name="snippet"),
        ),
        migrations.AlterField(
            model_name="snippet",
            name="snippet",
            field=models.TextField(blank=True, null=True, verbose_name="snippet"),
        ),
    ]
