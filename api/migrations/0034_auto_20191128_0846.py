# Generated by Django 2.0.12 on 2019-11-28 08:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_auto_20191127_0850'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fieldreport',
            old_name='gov_potentially_affected',
            new_name='gov_num_potentially_affected',
        ),
        migrations.RenameField(
            model_name='fieldreport',
            old_name='other_potentially_affected',
            new_name='other_num_potentially_affected',
        ),
    ]
