# Generated by Django 3.2.16 on 2022-10-24 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0044_alter_dref_modified_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dref',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, verbose_name='modified at'),
        ),
    ]