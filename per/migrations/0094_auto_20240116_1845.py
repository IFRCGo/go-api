# Generated by Django 3.2.23 on 2024-01-16 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0093_auto_20240116_1739'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opslearning',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='opslearning',
            name='organization_validated',
        ),
        migrations.RenameField(
            model_name='opslearning',
            old_name='organization2',
            new_name='organization',
        ),
        migrations.RenameField(
            model_name='opslearning',
            old_name='organization2_validated',
            new_name='organization_validated',
        ),
    ]
