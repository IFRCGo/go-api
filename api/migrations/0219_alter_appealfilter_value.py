# Generated by Django 4.2.19 on 2025-04-17 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0218_remove_event_title_remove_event_title_ar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appealfilter',
            name='value',
            field=models.CharField(max_length=100000, verbose_name='value'),
        ),
    ]
