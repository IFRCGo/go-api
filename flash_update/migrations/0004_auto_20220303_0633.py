# Generated by Django 2.2.27 on 2022-03-03 06:33

from django.db import migrations, models
import flash_update.models


class Migration(migrations.Migration):

    dependencies = [
        ('flash_update', '0003_flashupdateshare'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flashemailsubscriptions',
            name='share_with',
            field=models.CharField(choices=[('ifrc_secretariat', 'IFRC Secretariat'), ('rcrc_network', 'RCRC Network')], default=flash_update.models.FlashUpdate.FlashShareWith('ifrc_secretariat'), max_length=50, verbose_name='share with'),
        ),
        migrations.AlterField(
            model_name='flashupdate',
            name='share_with',
            field=models.CharField(blank=True, choices=[('ifrc_secretariat', 'IFRC Secretariat'), ('rcrc_network', 'RCRC Network')], max_length=50, null=True, verbose_name='share with'),
        ),
        migrations.AlterField(
            model_name='flashupdateshare',
            name='donor_groups',
            field=models.ManyToManyField(blank=True, to='flash_update.DonorGroup'),
        ),
        migrations.AlterField(
            model_name='flashupdateshare',
            name='donors',
            field=models.ManyToManyField(blank=True, to='flash_update.Donors'),
        ),
    ]
