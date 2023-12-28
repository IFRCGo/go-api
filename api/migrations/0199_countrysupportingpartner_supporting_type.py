# Generated by Django 3.2.23 on 2023-12-28 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0198_countrysupportingpartner'),
    ]

    operations = [
        migrations.AddField(
            model_name='countrysupportingpartner',
            name='supporting_type',
            field=models.IntegerField(blank=True, choices=[(0, 'Ifrc'), (1, 'International Partners')], null=True, verbose_name='Supporting Type'),
        ),
    ]
