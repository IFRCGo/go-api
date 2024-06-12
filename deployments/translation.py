from modeltranslation.translator import TranslationOptions, register

from .models import (
    DeployedPerson,
    PartnerSocietyActivities,
    PartnerSocietyDeployment,
    Personnel,
    PersonnelDeployment,
    Project,
    RegionalProject,
)


@register(DeployedPerson)
class DeployedPersonTO(TranslationOptions):
    fields = ("role",)


@register(Personnel)
class PersonnelTO(TranslationOptions):
    # fields = ('role',) is already provided by DeployedPerson (model parent class)
    pass


@register(PartnerSocietyDeployment)
class PartnerSocietyDeploymentTO(TranslationOptions):
    # fields = ('role',) is already provided by DeployedPerson (model parent class)
    pass


@register(PersonnelDeployment)
class PersonnelDeploymentTO(TranslationOptions):
    fields = ("comments",)


@register(PartnerSocietyActivities)
class PartnerSocietyActivitiesTO(TranslationOptions):
    fields = ("activity",)


@register(RegionalProject)
class RegionalProjectTO(TranslationOptions):
    fields = ("name",)


@register(Project)
class ProjectTO(TranslationOptions):
    fields = (
        "name",
        "description",
    )
