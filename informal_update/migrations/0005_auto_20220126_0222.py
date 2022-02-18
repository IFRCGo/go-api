# Generated by Django 2.2.25 on 2022-01-26 02:22

from django.db import migrations, models
import informal_update.models


class Migration(migrations.Migration):

    dependencies = [
        ('informal_update', '0004_auto_20220117_1110'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donors',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(blank=True, max_length=500, null=True)),
                ('first_name', models.CharField(blank=True, max_length=300, null=True)),
                ('last_name', models.CharField(blank=True, max_length=300, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('position', models.CharField(blank=True, max_length=300, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='informalemailsubscriptions',
            name='share_with',
            field=models.CharField(choices=[('ifrc_secretariat', 'IFRC Secretariat'), ('rcrc_network', 'RCRC Network')], default=informal_update.models.InformalUpdate.InformalShareWith('ifrc_secretariat'), max_length=50, verbose_name='share with'),
        ),
        migrations.AlterField(
            model_name='informalupdate',
            name='share_with',
            field=models.CharField(choices=[('ifrc_secretariat', 'IFRC Secretariat'), ('rcrc_network', 'RCRC Network')], default=informal_update.models.InformalUpdate.InformalShareWith('ifrc_secretariat'), max_length=50, verbose_name='share with'),
        ),
    ]
