# Generated by Django 3.2.19 on 2023-06-23 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0072_remove_overview_orientation_document'),
    ]

    operations = [
        migrations.AddField(
            model_name='overview',
            name='orientation_documents',
            field=models.ManyToManyField(blank=True, to='per.PerFile', verbose_name='orientation documents'),
        ),
    ]
