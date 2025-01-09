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

        # Get OpsLearning IDs that already have parent component
        with_parent_component_ops_learning_qs = OpsLearning.objects.filter(per_component=parent_component_14).values_list(
            "id", flat=True
        )

        # For per_component
        # Removing if already have parent component
        OpsLearning.per_component.through.objects.filter(
            formcomponent_id__in=sub_components_14_ids, opslearning_id__in=with_parent_component_ops_learning_qs
        ).delete()

        # Removing all Sub-Components except one and updating to parent component
        OpsLearning.per_component.through.objects.filter(formcomponent_id__in=sub_components_14_ids).exclude(
            id__in=OpsLearning.per_component.through.objects.filter(formcomponent_id__in=sub_components_14_ids).distinct(
                "opslearning_id"
            )
        ).delete()

        OpsLearning.per_component.through.objects.filter(formcomponent_id__in=sub_components_14_ids).update(
            formcomponent_id=parent_component_14.id
        )

        # For per_component_validated
        # Get OpsLearning IDs that already have parent component validated
        with_parent_component_validated_ops_learning_qs = OpsLearning.objects.filter(
            per_component_validated=parent_component_14
        ).values_list("id", flat=True)

        # Removing if already have parent component
        OpsLearning.per_component_validated.through.objects.filter(
            formcomponent_id__in=sub_components_14_ids, opslearning_id__in=with_parent_component_validated_ops_learning_qs
        ).delete()

        # Removing all Sub-Components except one and updating to parent component
        OpsLearning.per_component_validated.through.objects.filter(formcomponent_id__in=sub_components_14_ids).exclude(
            id__in=OpsLearning.per_component_validated.through.objects.filter(
                formcomponent_id__in=sub_components_14_ids
            ).distinct("opslearning_id")
        ).delete()

        OpsLearning.per_component_validated.through.objects.filter(formcomponent_id__in=sub_components_14_ids).update(
            formcomponent_id=parent_component_14.id
        )

        self.stdout.write(self.style.SUCCESS("Successfully migrated sub-components of component-14 to component-14"))
