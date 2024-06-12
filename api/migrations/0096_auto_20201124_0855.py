# Generated by Django 2.2.13 on 2020-11-24 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0095_auto_20201124_0813"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="additional_tab_name_ar",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Label for Additional Tab"),
        ),
        migrations.AddField(
            model_name="region",
            name="additional_tab_name_en",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Label for Additional Tab"),
        ),
        migrations.AddField(
            model_name="region",
            name="additional_tab_name_es",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Label for Additional Tab"),
        ),
        migrations.AddField(
            model_name="region",
            name="additional_tab_name_fr",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Label for Additional Tab"),
        ),
    ]
