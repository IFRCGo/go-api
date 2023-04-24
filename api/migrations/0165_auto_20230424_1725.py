# Generated by Django 3.2.18 on 2023-04-24 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0164_appealdocumenttype'),
    ]

    operations = [
        migrations.AddField(
            model_name='appealdocument',
            name='description',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='appealdocument',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.appealdocumenttype', verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='country',
            name='iso3',
            field=models.CharField(blank=True, max_length=3, null=True, unique=True, validators=[django.core.validators.RegexValidator('^[A-Z]*$', 'ISO must be uppercase')], verbose_name='ISO3'),
        ),
    ]
