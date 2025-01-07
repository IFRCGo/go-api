from django.core.management.base import BaseCommand

from per.models import FormComponent, OpsLearning


class Command(BaseCommand):
    help = "Migration of sub components of component 14 to component 14"

    def handle(self, *args, **kwargs):

        parent_component_14 = FormComponent.objects.filter(component_num=14, is_parent=True).first()
        sub_components_14 = FormComponent.objects.filter(component_num=14, is_parent__isnull=True)

        if not sub_components_14.exists():
            self.stdout.write(self.style.WARNING("No sub components found for component 14"))

            return

        sub_components_14_ids = sub_components_14.values_list("id", flat=True)

        ops_learnings = OpsLearning.objects.filter(
            per_component__in=sub_components_14_ids, per_component_validated__in=sub_components_14_ids
        )
        for ops_learning in ops_learnings:
            if ops_learning.is_validated:
                ops_learning.per_component_validated.remove(*sub_components_14_ids)
                ops_learning.per_component_validated.add(parent_component_14)
            ops_learning.per_component.remove(*sub_components_14_ids)
            ops_learning.per_component.add(parent_component_14)

            ops_learning.save()
        self.stdout.write(self.style.SUCCESS("Migration of sub components of component 14 to component 14 is done"))
