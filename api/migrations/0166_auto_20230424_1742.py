# Generated by Django 3.2.18 on 2023-04-24 17:42

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0165_auto_20230424_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='appealdocument',
            name='iso3',
            field=models.ForeignKey(db_column='iso3', null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.country', to_field='iso3', verbose_name='iso3'),
        ),
    ]
