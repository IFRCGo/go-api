# Generated by Django 2.2.24 on 2021-11-17 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0040_auto_20210920_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='visibility',
            field=models.CharField(choices=[('logged_in_user', 'Membership'), ('ifrc_only', 'IFRC Only'), ('public', 'Public'), ('ifrc_ns', 'IFRC_NS')], default='public', max_length=32, verbose_name='visibility'),
        ),
    ]
