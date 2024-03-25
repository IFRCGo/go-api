# Generated by Django 3.2.23 on 2024-02-09 06:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0020_fdrsannualincome'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountryKeyClimate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(verbose_name='year')),
                ('month', models.PositiveSmallIntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], verbose_name='month')),
                ('min_temp', models.FloatField(verbose_name='min temperature')),
                ('max_temp', models.FloatField(verbose_name='max temperature')),
                ('avg_temp', models.FloatField(verbose_name='average temperature')),
                ('precipitation', models.FloatField(verbose_name='precipitation')),
                ('overview', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='databank.countryoverview', verbose_name='country overview')),
            ],
            options={
                'verbose_name': 'Country Climate',
                'verbose_name_plural': 'Country Climate',
                'unique_together': {('overview', 'month', 'year')},
            },
        ),
    ]