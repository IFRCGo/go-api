from django.core.management.base import BaseCommand

from per.models import FormComponent, OpsLearning


class Command(BaseCommand):
    help = "Migration of sub components of component 14 to component 14"

    def handle(self, *args, **kwargs):
        parent_component_14 = FormComponent.objects.filter(component_num=14, is_parent=True)
        sub_components_14 = FormComponent.objects.filter(component_num=14, is_parent__isnull=True)

        if not sub_components_14.exists():
            self.stdout.write(self.style.WARNING("No sub components found for component 14"))

            return

        ops_learnings = OpsLearning.objects.filter(per_component__in=sub_components_14)
        for ops_learning in ops_learnings:
            if ops_learning.is_validated:
                sub_components_in_validated = ops_learning.per_component_validated.filter(id__in=sub_components_14)
                if sub_components_in_validated.exists():
                    ops_learning.per_component_validated.remove(*sub_components_14)
                    ops_learning.per_component_validated.add(parent_component_14)

            sub_components_in_per_component = ops_learning.per_component.filter(id__in=sub_components_14)
            if sub_components_in_per_component.exists():
                ops_learning.per_component.remove(*sub_components_14)
                ops_learning.per_component.add(parent_component_14)

            ops_learning.save()
            self.stdout.write(self.style.SUCCESS("Migration of sub components of component 14 to component 14 is done"))
