# Generated by Django 3.2.19 on 2023-06-05 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0058_auto_20230529_0806'),
    ]

    operations = [
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='identified_gaps',
            field=models.TextField(blank=True, help_text='Any identified gaps/limitations in the assessment', null=True, verbose_name='identified gaps'),
        ),
    ]