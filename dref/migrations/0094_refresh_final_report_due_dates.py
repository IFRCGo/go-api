from dateutil.relativedelta import relativedelta
from django.db import migrations


def refresh_final_report_due_dates(apps, schema_editor):
    Dref = apps.get_model("dref", "Dref")
    DrefOperationalUpdate = apps.get_model("dref", "DrefOperationalUpdate")
    database = schema_editor.connection.alias
    for dref in Dref.objects.using(database).all().iterator():
        end_date = dref.end_date
        if dref.appeal_code:
            latest_update = (
                DrefOperationalUpdate.objects.using(database)
                .filter(appeal_code=dref.appeal_code, date_of_approval__isnull=False)
                .order_by("-date_of_approval", "-operational_update_number", "-pk")
                .first()
            )
            if latest_update and latest_update.new_operational_end_date:
                end_date = latest_update.new_operational_end_date
        due_date = end_date + relativedelta(months=3) if end_date else None
        Dref.objects.using(database).filter(pk=dref.pk).update(final_report_due_date=due_date)


class Migration(migrations.Migration):
    dependencies = [
        ("dref", "0093_drefsummary_section_status"),
    ]

    operations = [
        migrations.RunPython(refresh_final_report_due_dates, migrations.RunPython.noop),
    ]
