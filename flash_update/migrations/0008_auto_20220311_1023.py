# Generated by Django 2.2.27 on 2022-03-11 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flash_update", "0007_auto_20220303_1116"),
    ]

    operations = [
        migrations.AddField(
            model_name="flashupdate",
            name="extracted_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="extracted at"),
        ),
        migrations.AddField(
            model_name="flashupdate",
            name="extracted_file",
            field=models.FileField(blank=True, null=True, upload_to="flash_update/pdf/", verbose_name="extracted file"),
        ),
    ]
