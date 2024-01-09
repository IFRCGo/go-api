# Generated by Django 3.2.23 on 2023-12-18 09:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0193_countrycapacitystrengthening'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountryOrganizationalCapacity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leadership_capacity', models.TextField(blank=True, null=True, verbose_name='Leadership Capacity')),
                ('youth_capacity', models.TextField(blank=True, null=True, verbose_name='Youth Capacity')),
                ('volunteer_capacity', models.TextField(blank=True, null=True, verbose_name='Volunteer Capacity')),
                ('financial_capacity', models.TextField(blank=True, null=True, verbose_name='Financial Capacity')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.country', verbose_name='Country')),
            ],
        ),
    ]