import django.db.models.deletion
from django.db import migrations, models

import api.models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0130_auto_20210615_0920"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    "UPDATE api_appealhistory SET dtype_id = api_appeal.dtype_id, status = api_appeal.status, needs_confirmation = api_appeal.needs_confirmation, code = api_appeal.code from api_appeal WHERE api_appeal.aid = api_appealhistory.aid"
                )
            ],
            reverse_sql=[("DELETE FROM api_appealhistory where valid_to = '2200-01-01'")],
        )
    ]
