# Generated by Django 2.2.13 on 2020-12-08 13:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0101_uppercase_iso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='country',
            name='iso',
            field=models.CharField(max_length=2, null=True, validators=[django.core.validators.RegexValidator('^[A-Z]*$', 'ISO must be uppercase')], verbose_name='ISO'),
        ),
        migrations.AlterField(
            model_name='country',
            name='iso3',
            field=models.CharField(max_length=3, null=True, validators=[django.core.validators.RegexValidator('^[A-Z]*$', 'ISO must be uppercase')], verbose_name='ISO3'),
        ),
        migrations.AlterField(
            model_name='district',
            name='country_iso',
            field=models.CharField(max_length=2, null=True, validators=[django.core.validators.RegexValidator('^[A-Z]*$', 'ISO must be uppercase')], verbose_name='country ISO2'),
        ),
    ]
