# Generated by Django 2.2.20 on 2021-07-01 06:35

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0131_appealhistory_fill_2'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('title_en', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_es', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_fr', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_ar', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('description', models.TextField(verbose_name='description')),
                ('description_en', models.TextField(null=True, verbose_name='description')),
                ('description_es', models.TextField(null=True, verbose_name='description')),
                ('description_fr', models.TextField(null=True, verbose_name='description')),
                ('description_ar', models.TextField(null=True, verbose_name='description')),
                ('url', models.URLField(verbose_name='url')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', related_query_name='link', to='api.Event', verbose_name='event')),
            ],
        ),
        migrations.CreateModel(
            name='EventFeaturedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('title_en', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_es', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_fr', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('title_ar', models.CharField(max_length=200, null=True, verbose_name='title')),
                ('description', models.TextField(verbose_name='description')),
                ('description_en', models.TextField(null=True, verbose_name='description')),
                ('description_es', models.TextField(null=True, verbose_name='description')),
                ('description_fr', models.TextField(null=True, verbose_name='description')),
                ('description_ar', models.TextField(null=True, verbose_name='description')),
                ('thumbnail', models.ImageField(help_text='Please maintain aspect ratio (3:4) of image while uploading', storage=django.core.files.storage.FileSystemStorage(location='media'), upload_to='event-featured-documents/thumbnail/', verbose_name='thumbnail')),
                ('file', models.FileField(storage=django.core.files.storage.FileSystemStorage(location='media'), upload_to='event-featured-documents/file/', verbose_name='file')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='featured_documents', related_query_name='featured_document', to='api.Event', verbose_name='event')),
            ],
        ),
    ]
