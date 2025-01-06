from django.db import migrations


def migrate_sub_components_to_component14(apps, schema_editor):
    FormComponent = apps.get_model("per", "FormComponent")
    OpsLearning = apps.get_model("per", "OpsLearning")

    component_14 = FormComponent.objects.filter(component_num=14)
    if component_14.exists():
        sub_components_14 = component_14.filter(component_letter__isnull=False)
        ops_learnings = OpsLearning.objects.filter(per_component__in=sub_components_14)
        for ops_learning in ops_learnings:
            if ops_learning.is_validated:
                ops_learning.per_component_validated.remove(*sub_components_14)
                ops_learning.per_component_validated.add(component_14.first())
            ops_learning.per_component.remove(*sub_components_14)
            ops_learning.per_component.add(component_14.first())

            ops_learning.save()
l

class Migration(migrations.Migration):

    dependencies = [("per", "0122_opslearningcacheresponse_and_more")]

    operations = [migrations.RunPython(migrate_sub_components_to_component14)]

