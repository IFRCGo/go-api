# Generated by Django 2.2.27 on 2022-06-13 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0012_auto_20220613_0911'),
    ]

    operations = [
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='photos',
            field=models.ManyToManyField(blank=True, related_name='photos_dref_operational_update', to='dref.DrefFile', verbose_name='images'),
        ),
    ]