# Generated by Django 2.2.13 on 2020-07-28 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0078_auto_20200721_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='independent',
            field=models.NullBooleanField(default=None, help_text='Is this an independent country?'),
        )
    ]
