# Generated by Django 2.2.13 on 2020-11-11 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0033_molnixtag'),
    ]

    operations = [
        migrations.AddField(
            model_name='personnel',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='personnel',
            name='molnix_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='personneldeployment',
            name='is_molnix',
            field=models.BooleanField(default=False),
        ),
    ]
