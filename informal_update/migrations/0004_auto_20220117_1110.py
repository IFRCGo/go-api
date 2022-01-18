# Generated by Django 2.2.25 on 2022-01-17 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('informal_update', '0003_informalemailsubscriptions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informalreferences',
            name='date',
            field=models.DateField(blank=True, verbose_name='date'),
        ),
        migrations.RemoveField(
            model_name='informalreferences',
            name='url',
        ),
        migrations.AddField(
            model_name='informalreferences',
            name='url',
            field=models.TextField(blank=True),
        ),
        migrations.DeleteModel(
            name='ReferenceUrls',
        ),
    ]
