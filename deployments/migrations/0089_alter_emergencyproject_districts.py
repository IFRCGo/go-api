# Generated by Django 4.2.10 on 2024-02-11 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0188_auto_20240109_0508'),
        ('deployments', '0088_alter_project_visibility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emergencyproject',
            name='districts',
            field=models.ManyToManyField(blank=True, related_name='+', to='api.district', verbose_name='Districts'),
        ),
    ]
