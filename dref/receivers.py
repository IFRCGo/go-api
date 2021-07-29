from dref.models import Dref
from django.db.models.signals import m2m_changed
from django.core.exceptions import ValidationError


def planned_interventions_changed(sender, **kwargs):
    if kwargs['instance'].planned_interventions.count() >= 5:
        raise ValidationError("You can't assign more than five planned interventions")


m2m_changed.connect(planned_interventions_changed, sender=Dref.planned_interventions.through)
