# Generated by Django 2.2.20 on 2021-08-29 23:45

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import dref.models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0004_auto_20210827_0547'),
    ]

    operations = [
        migrations.CreateModel(
            name='DrefFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media'), upload_to=dref.models.dref_path, verbose_name='file')),
            ],
            options={
                'verbose_name': 'dref file',
                'verbose_name_plural': 'dref files',
            },
        ),
        migrations.AddField(
            model_name='dref',
            name='event_map',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_map', to='dref.DrefFile', verbose_name='event map'),
        ),
        migrations.AddField(
            model_name='dref',
            name='images',
            field=models.ManyToManyField(blank=True, related_name='images', to='dref.DrefFile', verbose_name='images'),
        ),
    ]
