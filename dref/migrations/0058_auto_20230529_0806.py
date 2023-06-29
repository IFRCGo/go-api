# Generated by Django 3.2.19 on 2023-05-29 08:06

from django.db import migrations
from dref.models import Dref as Status

class Migration(migrations.Migration):

    def update_dref_status(apps, schema_editor):
        # Update all the `is_published` dref to status completed
        # – all other to in_progress (ongoing)
        Dref = apps.get_model('dref', 'Dref')
        DrefOperationalUpdate = apps.get_model('dref', 'DrefOperationalUpdate')
        DrefFinalReport = apps.get_model('dref', 'DrefFinalReport')
        drefs = Dref.objects.all()
        op_updates = DrefOperationalUpdate.objects.all()
        final_reports = DrefFinalReport.objects.all()
        # drefs
        for dref in drefs:
            if dref.is_published:
                dref.status = Status.Status.COMPLETED
            else:
                dref.status = Status.Status.IN_PROGRESS
            dref.save(update_fields=['status'])

        # dref operational update
        for op in op_updates:
            if op.is_published:
                op.status = Status.Status.COMPLETED
            else:
                op.status = Status.Status.IN_PROGRESS
            op.save(update_fields=['status'])

        # dref final report
        for final_report in final_reports:
            if final_report.is_published:
                final_report.status = Status.Status.COMPLETED
            else:
                final_report.status = Status.Status.IN_PROGRESS
            final_report.save(update_fields=['status'])

    dependencies = [
        ('dref', '0057_auto_20230526_0414'),
    ]

    operations = [
        migrations.RunPython(
            update_dref_status,
            reverse_code=migrations.RunPython.noop
        ),
    ]