# Generated by Django 2.2.27 on 2022-03-22 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0149_auto_20220318_0413'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='emergency_response_contact_email',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='emergency response contact email'),
        ),
    ]
