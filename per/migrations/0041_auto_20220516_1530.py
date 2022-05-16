# Generated by Django 3.2 on 2022-05-16 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0040_auto_20201214_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workplan',
            name='prioritization',
            field=models.IntegerField(choices=[(0, 'low'), (1, 'medium'), (2, 'high')], default=0, verbose_name='prioritization'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='status',
            field=models.IntegerField(choices=[(0, 'standby'), (1, 'ongoing'), (2, 'cancelled'), (3, 'delayed'), (4, 'pending'), (5, 'need improvements'), (6, 'finished'), (7, 'approved'), (8, 'closed')], default=0, verbose_name='status'),
        ),
    ]
