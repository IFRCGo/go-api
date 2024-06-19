# Generated by Django 4.2.13 on 2024-05-23 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0117_auto_20240522_0529"),
    ]

    operations = [
        migrations.AddField(
            model_name="percomponentrating",
            name="title_ar",
            field=models.CharField(max_length=250, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="percomponentrating",
            name="title_en",
            field=models.CharField(max_length=250, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="percomponentrating",
            name="title_es",
            field=models.CharField(max_length=250, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="percomponentrating",
            name="title_fr",
            field=models.CharField(max_length=250, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="percomponentrating",
            name="translation_module_original_language",
            field=models.CharField(
                choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                default="en",
                help_text="Language used to create this entity",
                max_length=2,
                verbose_name="Entity Original language",
            ),
        ),
        migrations.AddField(
            model_name="percomponentrating",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
    ]