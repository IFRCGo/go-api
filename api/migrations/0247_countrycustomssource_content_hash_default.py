from django.db import migrations, models


def populate_empty_content_hash(apps, schema_editor):
    CountryCustomsSource = apps.get_model("api", "CountryCustomsSource")
    CountryCustomsSource.objects.filter(content_hash__isnull=True).update(content_hash="")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0246_merge_20260310_1324"),
    ]

    operations = [
        migrations.RunPython(populate_empty_content_hash, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="countrycustomssource",
            name="content_hash",
            field=models.CharField(blank=True, default="", help_text="Hash of source's evidence snippets", max_length=64),
        ),
    ]