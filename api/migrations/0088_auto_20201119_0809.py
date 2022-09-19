# Generated by Django 2.2.13 on 2020-11-19 08:09

import api.models
from django.db import migrations, models
import django.db.models.deletion
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0087_auto_20200918_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='additional_tab_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Label for Extra Tab'),
        ),
        migrations.AddField(
            model_name='region',
            name='additional_tab_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Label for Additional Tab'),
        ),
        migrations.AlterField(
            model_name='event',
            name='num_displaced',
            field=models.IntegerField(blank=True, null=True, verbose_name='number of displaced'),
        ),
        migrations.CreateModel(
            name='RegionProfileSnippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255)),
                ('snippet', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_en', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_es', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_fr', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_ar', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('visibility', models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices, verbose_name='visibility')),
                ('position', models.IntegerField(default=3, choices=api.models.PositionType.choices, verbose_name='position')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_snippets', to='api.Region', verbose_name='region')),
            ],
            options={
                'verbose_name': 'region profile snippet',
                'verbose_name_plural': 'region profile snippets',
                'ordering': ('position', 'id'),
            },
        ),
        migrations.CreateModel(
            name='RegionPreparednessSnippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255)),
                ('snippet', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_en', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_es', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_fr', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_ar', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('visibility', models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices, verbose_name='visibility')),
                ('position', models.IntegerField(default=3, choices=api.models.PositionType.choices, verbose_name='position')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preparedness_snippets', to='api.Region', verbose_name='region')),
            ],
            options={
                'verbose_name': 'region preparedness snippet',
                'verbose_name_plural': 'region preparedness snippets',
                'ordering': ('position', 'id'),
            },
        ),
        migrations.CreateModel(
            name='RegionEmergencySnippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255)),
                ('snippet', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_en', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_es', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_fr', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('snippet_ar', tinymce.models.HTMLField(blank=True, null=True, verbose_name='snippet')),
                ('visibility', models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices, verbose_name='visibility')),
                ('position', models.IntegerField(default=3, choices=api.models.PositionType.choices, verbose_name='position')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emergency_snippets', to='api.Region', verbose_name='region')),
            ],
            options={
                'verbose_name': 'region emergencies snippet',
                'verbose_name_plural': 'region emergencies snippets',
                'ordering': ('position', 'id'),
            },
        ),
        migrations.CreateModel(
            name='RegionAdditionalLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('show_in_go', models.BooleanField(default=False, help_text='Show link contents within GO')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_links', to='api.Region')),
            ],
        ),
    ]
