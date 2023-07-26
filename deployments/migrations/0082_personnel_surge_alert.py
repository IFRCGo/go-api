# Generated by Django 3.2.20 on 2023-07-26 10:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0013_auto_20230410_0720'),
        ('deployments', '0081_merge_20230614_0804'),
    ]

    operations = [
        migrations.AddField(
            model_name='personnel',
            name='surge_alert',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='notifications.surgealert', verbose_name='surge alert'),
        ),
    ]
