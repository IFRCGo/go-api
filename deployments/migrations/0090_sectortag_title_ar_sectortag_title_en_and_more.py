# Generated by Django 4.2.16 on 2024-11-06 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0089_alter_emergencyproject_districts"),
    ]

    operations = [
        migrations.AddField(
            model_name="sectortag",
            name="title_ar",
            field=models.CharField(max_length=255, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="sectortag",
            name="title_en",
            field=models.CharField(max_length=255, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="sectortag",
            name="title_es",
            field=models.CharField(max_length=255, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="sectortag",
            name="title_fr",
            field=models.CharField(max_length=255, null=True, verbose_name="title"),
        ),
        migrations.AddField(
            model_name="sectortag",
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
            model_name="sectortag",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
    ]
