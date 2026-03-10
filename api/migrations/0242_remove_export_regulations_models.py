# Generated manually - remove export regulations models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0241_export_regulations_models'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CountryExportEvidenceSnippet',
        ),
        migrations.DeleteModel(
            name='CountryExportSource',
        ),
        migrations.DeleteModel(
            name='CountryExportSnapshot',
        ),
    ]
