from modeltranslation.translator import register, TranslationOptions
from .models import (
    PartnerSocietyActivities,
    PersonnelDeployment,
    DeployedPerson,
    RegionalProject,
    Project,
)


@register(DeployedPerson)
class DeployedPersonTO(TranslationOptions):
    fields = ('role',)


@register(PersonnelDeployment)
class PersonnelDeploymentTO(TranslationOptions):
    fields = ('comments',)


@register(PartnerSocietyActivities)
class PartnerSocietyActivitiesTO(TranslationOptions):
    fields = ('activity',)


@register(RegionalProject)
class RegionalProjectTO(TranslationOptions):
    fields = ('name',)


@register(Project)
class ProjectTO(TranslationOptions):
    fields = ('name',)
