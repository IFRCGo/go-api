# Generated by Django 2.2.13 on 2020-11-30 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0099_auto_20201127_1048"),
    ]

    operations = [
        migrations.AlterField(
            model_name="country",
            name="fdrs",
            field=models.CharField(blank=True, max_length=6, null=True, verbose_name="FDRS"),
        ),
    ]
