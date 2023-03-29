# Generated by Django 3.2.18 on 2023-03-09 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0075_alter_project_primary_sector'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sector',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='sectortag',
            name='slug',
        ),
        migrations.AddField(
            model_name='sector',
            name='color',
            field=models.CharField(blank=True, max_length=7, null=True, verbose_name='color'),
        ),
        migrations.AddField(
            model_name='sector',
            name='is_deprecated',
            field=models.BooleanField(default=False, help_text='Is this a deprecated sector?'),
        ),
        migrations.AddField(
            model_name='sectortag',
            name='color',
            field=models.CharField(blank=True, max_length=7, null=True, verbose_name='color'),
        ),
        migrations.AddField(
            model_name='sectortag',
            name='is_deprecated',
            field=models.BooleanField(default=False, help_text='Is this a deprecated sector tag?'),
        ),
    ]