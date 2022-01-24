# Generated manually on 2022-01-24 17:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0042_personnel_country_to'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[("update deployments_personnel " +
                  "set country_to_id=d.country_id " +
                  "from deployments_personnel a " +
                  "join deployments_personneldeployment b on a.deployment_id = b.id " +
                  "join api_event c on b.event_deployed_to_id = c.id " +
                  "join api_event_countries d on c.id = d.event_id " +
                  "where deployments_personnel.deployedperson_ptr_id = a.deployedperson_ptr_id")],
            reverse_sql=[("update deployments_personnel set country_to_id=NULL")],
        )
    ]
