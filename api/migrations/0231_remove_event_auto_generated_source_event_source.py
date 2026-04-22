
from django.db import migrations, models


def migrate_sources(apps, schema_editor):
    """
    Populate the source field for Event records:
    - Non auto generated events are mapped to MANUAL_INPUT
    - Events that are auto generated and have auto_generated_source are mapped to the corresponding enum value
    - Events that are auto generated and auto_generated_source is null or unrecognized are mapped to UNKNOWN
    """
    
    Model = apps.get_model("api", "Event")
    for obj in Model.objects.iterator():
        if not obj.auto_generated:
            value = 100

        else:
            src = (obj.auto_generated_source or "").lower()

            if "who.int" in src:
                value = 120
            elif "gdacs" in src:
                value = 110
            elif "field report dmis ingest" in src:
                value = 130
            elif "field report admin" in src:
                value = 140
            elif "appeal" in src:
                value = 150
            elif "new field report" in src:
                value = 160
            else:
                value = 180

        obj.source = value
        obj.save(update_fields=["source"])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0230_alter_districtgeoms_district'),
    ]

    operations = [
        
        migrations.AddField(
            model_name='event',
            name='source',
            field=models.IntegerField(choices=[(100, 'Manual input'), (110, 'GDACs scraper'), (120, 'WHO scraper'), (130, 'Field report DMIS ingest'), (140, 'Field report admin'), (150, 'Appeal admin'), (160, 'New field report'), (170, 'DREF'), (180, 'Unknown')], default=100, verbose_name='Event source'),
        ),
        migrations.RunPython(migrate_sources,reverse_code=migrations.RunPython.noop),
        
        migrations.RemoveField(
            model_name='event',
            name='auto_generated_source',
        ),
    ]
