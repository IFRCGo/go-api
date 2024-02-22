# Generated by Django 3.2.23 on 2024-02-20 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0189_auto_20240219_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminkeyfigure',
            name='deck_ar',
            field=models.CharField(max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='adminkeyfigure',
            name='deck_en',
            field=models.CharField(max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='adminkeyfigure',
            name='deck_es',
            field=models.CharField(max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='adminkeyfigure',
            name='deck_fr',
            field=models.CharField(max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='adminkeyfigure',
            name='translation_module_original_language',
            field=models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('ar', 'Arabic')], default='en', help_text='Language used to create this entity', max_length=2, verbose_name='Entity Original language'),
        ),
        migrations.AddField(
            model_name='adminkeyfigure',
            name='translation_module_skip_auto_translation',
            field=models.BooleanField(default=False, help_text='Skip auto translation operation for this entity?', verbose_name='Skip auto translation'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='deck_ar',
            field=models.CharField(help_text='key figure units', max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='deck_en',
            field=models.CharField(help_text='key figure units', max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='deck_es',
            field=models.CharField(help_text='key figure units', max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='deck_fr',
            field=models.CharField(help_text='key figure units', max_length=50, null=True, verbose_name='deck'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='translation_module_original_language',
            field=models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('ar', 'Arabic')], default='en', help_text='Language used to create this entity', max_length=2, verbose_name='Entity Original language'),
        ),
        migrations.AddField(
            model_name='keyfigure',
            name='translation_module_skip_auto_translation',
            field=models.BooleanField(default=False, help_text='Skip auto translation operation for this entity?', verbose_name='Skip auto translation'),
        ),
    ]