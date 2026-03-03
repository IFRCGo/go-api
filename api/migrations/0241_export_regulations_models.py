# Generated manually for export regulations models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0240_countrycustomsevidencesnippet_countrycustomssnapshot_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountryExportSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('country_name', models.CharField(db_index=True, max_length=255)),
                ('is_current', models.BooleanField(default=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('model_name', models.CharField(default='gpt-4', max_length=100)),
                ('confidence', models.CharField(choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], default='Medium', max_length=20)),
                ('summary_text', models.TextField(blank=True, default='')),
                ('current_situation_bullets', models.JSONField(default=list, help_text='Array of bullet point strings')),
                ('evidence_hash', models.CharField(blank=True, help_text='Hash of all source hashes', max_length=64)),
                ('search_query', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('partial', 'Partial'), ('failed', 'Failed')], default='success', max_length=20)),
                ('error_message', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Country Export Snapshot',
                'verbose_name_plural': 'Country Export Snapshots',
            },
        ),
        migrations.CreateModel(
            name='CountryExportSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rank', models.PositiveSmallIntegerField(help_text='Ranking by total score (1-3)')),
                ('url', models.URLField(max_length=2048)),
                ('title', models.CharField(max_length=500)),
                ('publisher', models.CharField(blank=True, max_length=255)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('retrieved_at', models.DateTimeField(auto_now_add=True)),
                ('authority_score', models.SmallIntegerField(default=0)),
                ('freshness_score', models.SmallIntegerField(default=0)),
                ('relevance_score', models.SmallIntegerField(default=0)),
                ('specificity_score', models.SmallIntegerField(default=0)),
                ('total_score', models.SmallIntegerField(default=0)),
                ('content_hash', models.CharField(blank=True, help_text="Hash of source's evidence snippets", max_length=64)),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='api.countryexportsnapshot')),
            ],
            options={
                'verbose_name': 'Country Export Source',
                'verbose_name_plural': 'Country Export Sources',
                'ordering': ['snapshot', 'rank'],
            },
        ),
        migrations.CreateModel(
            name='CountryExportEvidenceSnippet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snippet_order', models.PositiveSmallIntegerField()),
                ('snippet_text', models.TextField()),
                ('claim_tags', models.JSONField(blank=True, default=list, help_text='Optional: array of tags')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snippets', to='api.countryexportsource')),
            ],
            options={
                'verbose_name': 'Country Export Evidence Snippet',
                'verbose_name_plural': 'Country Export Evidence Snippets',
                'ordering': ['source', 'snippet_order'],
            },
        ),
        migrations.AddIndex(
            model_name='countryexportsnapshot',
            index=models.Index(fields=['country_name', '-generated_at'], name='export_country_date_idx'),
        ),
        migrations.AddConstraint(
            model_name='countryexportsnapshot',
            constraint=models.UniqueConstraint(condition=models.Q(('is_current', True)), fields=('country_name',), name='unique_current_country_export_snapshot'),
        ),
        migrations.AddIndex(
            model_name='countryexportsource',
            index=models.Index(fields=['snapshot', 'rank'], name='export_source_rank_idx'),
        ),
        migrations.AddIndex(
            model_name='countryexportevidencesnippet',
            index=models.Index(fields=['source', 'snippet_order'], name='export_snippet_order_idx'),
        ),
    ]
