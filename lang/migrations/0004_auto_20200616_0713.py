# Generated by Django 2.2.13 on 2020-06-16 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lang", "0003_auto_20200610_0911"),
    ]

    operations = [
        migrations.AlterField(
            model_name="string",
            name="hash",
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name="hash"),
        ),
        migrations.AlterField(
            model_name="string",
            name="key",
            field=models.CharField(max_length=255, verbose_name="key"),
        ),
        migrations.AlterField(
            model_name="string",
            name="language",
            field=models.CharField(
                choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                max_length=8,
                verbose_name="language",
            ),
        ),
        migrations.AlterField(
            model_name="string",
            name="value",
            field=models.TextField(verbose_name="value"),
        ),
        migrations.DeleteModel(
            name="Language",
        ),
    ]
