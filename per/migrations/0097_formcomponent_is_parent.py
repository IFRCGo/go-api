# Generated by Django 3.2.23 on 2024-01-18 04:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0096_migrate_formdata_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='formcomponent',
            name='is_parent',
            field=models.BooleanField(blank=True, null=True, verbose_name='Is parent'),
        ),
    ]
