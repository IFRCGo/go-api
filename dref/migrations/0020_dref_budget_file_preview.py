# Generated by Django 2.2.24 on 2021-12-23 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0019_dref_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='dref',
            name='budget_file_preview',
            field=models.FileField(blank=True, null=True, upload_to='dref/images/', verbose_name='budget file preview'),
        ),
    ]
