# Generated by Django 2.2.27 on 2022-04-18 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lang", "0004_auto_20200616_0713"),
    ]

    operations = [
        migrations.AddField(
            model_name="string",
            name="page_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Page name"),
        ),
    ]
