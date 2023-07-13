# Generated by Django 3.2.20 on 2023-07-13 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0063_merge_20230628_1022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dref',
            name='disability_people_per',
            field=models.FloatField(blank=True, help_text='Estimated % people disability', null=True, verbose_name='disability people per'),
        ),
        migrations.AlterField(
            model_name='dref',
            name='people_per_local',
            field=models.FloatField(blank=True, help_text='Estimated % people Rural', null=True, verbose_name='people per local'),
        ),
        migrations.AlterField(
            model_name='dref',
            name='people_per_urban',
            field=models.FloatField(blank=True, help_text='Estimated % people Urban', null=True, verbose_name='people per urban'),
        ),
    ]