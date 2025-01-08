from django.core.management.base import BaseCommand

from per.models import FormComponent, OpsLearning


class Command(BaseCommand):
    help = "Migration of sub components of component 14 to component 14"

    def handle(self, *args, **kwargs):

        parent_component_14 = FormComponent.objects.filter(component_num=14, is_parent=True).first()

        if not parent_component_14:
            self.stdout.write(self.style.ERROR("No parent component found for component 14"))
            return

        sub_components_14_ids = FormComponent.objects.filter(component_num=14, is_parent__isnull=True).values_list(
            "id", flat=True
        )

        if not sub_components_14_ids.exists():
            self.stdout.write(self.style.ERROR("No sub components found for component 14"))
            return

        with_parent_component_ops_learning_qs = OpsLearning.objects.filter(per_component=parent_component_14).values_list(
            "id", flat=True
        )

        # updating per_component for OpsLearning
        OpsLearning.per_component.through.objects.filter(formcomponent_id__in=sub_components_14_ids).exclude(
            opslearning_id__in=with_parent_component_ops_learning_qs
        ).update(formcomponent_id=parent_component_14.id)

        # Cleanup
        OpsLearning.per_component.through.objects.filter(
            formcomponent_id__in=sub_components_14_ids,
        ).delete()

        # updating per_component_validated for validated OpsLearning
        OpsLearning.per_component_validated.through.objects.filter(formcomponent_id__in=sub_components_14_ids).exclude(
            opslearning_id__in=with_parent_component_ops_learning_qs
        ).update(formcomponent_id=parent_component_14.id)

        # Cleanup
        OpsLearning.per_component_validated.through.objects.filter(
            formcomponent_id__in=sub_components_14_ids,
        ).delete()

        self.stdout.write(self.style.SUCCESS("Successfully migrated sub-components of component-14 to component-14"))
