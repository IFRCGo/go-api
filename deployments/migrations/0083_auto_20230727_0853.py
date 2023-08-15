# Generated by Django 3.2.20 on 2023-07-27 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0082_personnel_surge_alert'),
    ]

    operations = [
        migrations.CreateModel(
            name='MolnixTagGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('molnix_id', models.IntegerField()),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('is_deprecated', models.BooleanField(default=False, help_text='Is this a deprecated group?')),
            ],
            options={
                'verbose_name': 'Molnix Tag Group',
                'verbose_name_plural': 'Molnix Tag Groups',
            },
        ),
        migrations.AddField(
            model_name='molnixtag',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='groups', to='deployments.MolnixTagGroup'),
        ),
    ]
