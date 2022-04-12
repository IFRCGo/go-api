# Generated by Django 2.2.27 on 2022-04-12 07:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0151_merge_20220325_1027'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewFieldReportInCountry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Country', verbose_name='country')),
            ],
        ),
    ]
