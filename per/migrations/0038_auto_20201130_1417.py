# Generated by Django 2.2.13 on 2020-11-30 14:17

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0037_formquestion_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='formquestion',
            name='description_ar',
            field=tinymce.models.HTMLField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='formquestion',
            name='description_en',
            field=tinymce.models.HTMLField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='formquestion',
            name='description_es',
            field=tinymce.models.HTMLField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='formquestion',
            name='description_fr',
            field=tinymce.models.HTMLField(blank=True, null=True, verbose_name='description'),
        ),
    ]
