# Generated by Django 3.2.23 on 2024-01-09 04:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0201_country_disaster_law_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='countryorganizationalcapacity',
            name='country',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='api.country', verbose_name='Country'),
        ),
    ]
