# Generated by Django 3.2.25 on 2024-05-22 05:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0116_auto_20240521_0815'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='percomponentrating',
            name='title_ar',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='title_en',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='title_es',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='title_fr',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='translation_module_original_language',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='translation_module_skip_auto_translation',
        ),
    ]
