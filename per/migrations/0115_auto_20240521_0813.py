# Generated by Django 3.2.25 on 2024-05-21 08:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0114_auto_20240521_0801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='percomponentrating',
            name='value_ar',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='value_en',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='value_es',
        ),
        migrations.RemoveField(
            model_name='percomponentrating',
            name='value_fr',
        ),
    ]
