from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import IntEnum, EnumIntegerField

from api.models import (
    Country,
    DisasterType,
    District
)
from api.storage import get_storage


def dref_document_path(instance, filename):
    return 'dref/%s/%s' % (instance.iso, filename)


class NationalSocietyAction(models.Model):
    title = models.CharField(verbose_name=_('title'), max_length=255)
    description = models.TextField(verbose_name=_('description'), blank=True)

    class Meta:
        verbose_name = _('national society action')
        verbose_name_plural = _('national society actions')


class IdentifiedNeed(models.Model):

    title = models.CharField(verbose_name=_('title'), max_length=255, help_text=_('Title of identified needs'))
    description = models.TextField(verbose_name=_('description'), blank=True)

    class Meta:
        verbose_name = _('identified need')
        verbose_name_plural = _('identified needs')


class PlannedIntervention(models.Model):
    title = models.CharField(verbose_name=_('title'), max_length=255, help_text=_('Title of identified needs'))
    description = models.TextField(verbose_name=_('description'), blank=True)
    budget = models.IntegerField(verbose_name=_('budget'), blank=True, null=True)

    class Meta:
        verbose_name = _('planned intervention')
        verbose_name_plural = _('planned interventions')


class Dref(models.Model):

    class OnsetType(IntEnum):
        ANTICIPATORY = 0
        IMMINENT = 1
        SLOW = 2
        SUDDEN_ONSET = 3

        class Labels:
            ANTICIPATORY = _('Anticipatory')
            IMMINENT = _('Imminent')
            SLOW = _('Slow')
            SUDDEN_ONSET = _('Sudden Onset')

    class DisasterCategory(IntEnum):
        YELLOW = 0
        ORANGE = 1
        RED = 2

        class Labels:
            YELLOW = _('Yellow')
            ORANGE = _('Orange')
            RED = _('Red')

    class Status(IntEnum):
        IN_PROGESS = 0
        COMPLETED = 1

        class Labels:
            IN_PROGESS = _('In Progress')
            COMPLETED = _('Completed')

    title = models.CharField(verbose_name=_('title'), max_length=255)
    national_society = models.ForeignKey(
        Country, verbose_name=_('national_society'),
        blank=True, null=True,
        on_delete=models.SET_NULL)
    disaster_type = models.ForeignKey(
        DisasterType, verbose_name=_('disaster type'),
        blank=True, null=True,
        on_delete=models.SET_NULL)
    type_of_onset = EnumIntegerField(OnsetType, verbose_name=_('onset type'))
    disaster_category_level = EnumIntegerField(DisasterCategory, verbose_name=_('disaster category level'))
    status = EnumIntegerField(Status, verbose_name=_('status'))
    num_assisted = models.IntegerField(verbose_name=_('number of assisted'), blank=True, null=True)
    num_affected = models.IntegerField(verbose_name=_('number of affected'), blank=True, null=True)
    amount_requested = models.IntegerField(verbose_name=_('amount requested'), blank=True, null=True)
    emergency_appeal_planned = models.BooleanField(verbose_name=_('emergency appeal planned '), default=False)
    document = models.FileField(
        verbose_name=_('document'), null=True, blank=True, upload_to=dref_document_path, storage=get_storage()
    )
    disaster_date = models.DateField(verbose_name=_('disaster date'), null=True, blank=True)
    ns_respond_date = models.DateField(verbose_name=_('ns respond date'), null=True, blank=True)
    ns_respond_text = models.TextField(verbose_name=_('ns respond text'), blank=True)
    affect_same_population = models.BooleanField(
        default=False, help_text=_('Has a similar event affected the same population?')
    )
    affect_same_communities = models.BooleanField(
        default=False, help_text=_('Did it affect the same communities?')
    )
    affect_same_communities_text = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=_('affect same communities text')
    )
    ns_respond = models.BooleanField(
        default=False, help_text=_('Did NS respond')
    )
    ns_request = models.BooleanField(
        default=False, help_text=_('Did NS request a Dref?')
    )
    ns_request_text = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=_('ns request text')
    )
    lessons_learned = models.TextField(verbose_name=_('lessons learned'), blank=True)
    event_description = models.TextField(verbose_name=_('event description'), blank=True)
    image = models.ImageField(
        verbose_name=_('image'), null=True, blank=True, upload_to='dref/%Y/%m/%d/', storage=get_storage()
    )
    anticipatory_actions = models.TextField(
        verbose_name=_('anaticipatory actions'), blank=True,
        help_text=_('Description of anticipatory actions or imminent disaster')
    )
    event_scope = models.TextField(
        verbose_name=_('event scope'), blank=True,
        help_text=_('Scope and scale of event')
    )
    national_society_actions = models.ManyToManyField(
        NationalSocietyAction, verbose_name=_('national society actions'),
        blank=True
    )
    government_requested_assistance = models.BooleanField(
        default=False, help_text=_('Has government requested assistance')
    )
    government_requested_assistance_date = models.DateField(
        verbose_name=_('government requested assistance date'),
        null=True, blank=True
    )
    national_authorities = models.TextField(verbose_name=_('national authorities'), blank=True)
    rcrc_partners = models.TextField(verbose_name=_('rcrc partners'), blank=True)
    icrc = models.TextField(verbose_name=_('icrc'), blank=True)
    un_or_other = models.TextField(verbose_name=_('un or other'), blank=True)
    major_coordination_mechanism = models.TextField(
        verbose_name=_('major coordination mechanism'), blank=True,
        help_text=_('List major coordination mechanisms in place'))
    needs_identified = models.ManyToManyField(
        IdentifiedNeed, verbose_name=_('needs identified'),
        blank=True
    )
    identified_gaps = models.TextField(
        verbose_name=_('identified gaps'), blank=True,
        help_text=_('Any identified gaps/limitations in the assessment')
    )
    people_assisted = models.TextField(verbose_name=_('people assisted'), blank=True)
    selection_criteria = models.TextField(
        verbose_name=_('selection criteria'), blank=True,
        help_text=_('Selection criteria for affected people')
    )
    entity_affected = models.TextField(
        verbose_name=_('entity affected'), blank=True,
        help_text=_('Protection, gender, Inclusion affected in this process')
    )
    community_involved = models.TextField(
        verbose_name=_('community involved'), blank=True,
        help_text=_('Community been involved in the analysis of the process')
    )
    women = models.IntegerField(verbose_name=_('women'), blank=True, null=True)
    men = models.IntegerField(verbose_name=_('men'), blank=True, null=True)
    girls = models.IntegerField(
        verbose_name=_('girls'), help_text=_('Girls under 18'),
        blank=True, null=True
    )
    boys = models.IntegerField(
        verbose_name=_('boys'), help_text=_('Boys under 18'),
        blank=True, null=True
    )
    disability_people_per = models.DecimalField(
        verbose_name=_('disability people per'), help_text=_('Estimated % people disability'),
        blank=True, null=True,
        max_digits=3, decimal_places=1
    )
    people_per = models.DecimalField(
        verbose_name=_('people per'), help_text=_('Estimated % people Urban/Rural'),
        blank=True, null=True,
        max_digits=3, decimal_places=1
    )
    displaced_people = models.IntegerField(
        verbose_name=_('displaced people'), help_text=_('Estimated number of displaced people'),
        blank=True, null=True
    )
    operation_objective = models.TextField(
        verbose_name=_('operation objective'), help_text=_('Overall objective of the operation'),
        blank=True
    )
    response_strategy = models.TextField(verbose_name=_('response strategy'), blank=True)
    planned_interventions = models.ManyToManyField(
        PlannedIntervention,
        verbose_name=_('planned intervention'), blank=True
    )
    secretariat_service = models.TextField(verbose_name=_('secretariat service'), blank=True)
    national_society_strengthening = models.TextField(verbose_name=_('nationa society strengthening'), blank=True)
    ns_request_date = models.DateField(verbose_name=_('ns request date'), null=True, blank=True)
    submission_to_geneva = models.DateField(verbose_name=_('submission to geneva'), null=True, blank=True)
    date_of_approval = models.DateField(verbose_name=_('date of approval'), null=True, blank=True)
    start_date = models.DateField(verbose_name=_('start date'), null=True, blank=True)
    end_date = models.DateField(verbose_name=_('end date'), null=True, blank=True)
    publishing_date = models.DateField(verbose_name=_('publishing date'), null=True, blank=True)
    operation_timeframe = models.IntegerField(verbose_name=_('operation timeframe'), null=True, blank=True)
    appeal_code = models.CharField(verbose_name=_('appeal code'), max_length=255, null=True, blank=True)
    glide_code = models.CharField(verbose_name=_('glide number'), max_length=255, null=True, blank=True)
    appeal_manager_name = models.CharField(
        verbose_name=_('appeal manager name'), max_length=255,
        null=True, blank=True
    )
    appeal_manager_email = models.CharField(
        verbose_name=_('appeal manager email'), max_length=255,
        null=True, blank=True
    )
    project_manager_name = models.CharField(
        verbose_name=_('project manager name'), max_length=255,
        null=True, blank=True
    )
    project_manager_email = models.CharField(
        verbose_name=_('project manager email'), max_length=255,
        null=True, blank=True
    )
    national_society_contact_name = models.CharField(
        verbose_name=_('national society contact name'), max_length=255,
        null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_('national society contact email'), max_length=255,
        null=True, blank=True
    )
    media_contact_name = models.CharField(
        verbose_name=_('media contact name'), max_length=255,
        null=True, blank=True
    )
    media_contact_email = models.CharField(
        verbose_name=_('media contact email'), max_length=255,
        null=True, blank=True
    )
    ifrc_emergency_name = models.CharField(
        verbose_name=_('ifrc emergency name'), max_length=255,
        null=True, blank=True
    )
    ifrc_emergency_email = models.CharField(
        verbose_name=_('ifrc emergency email'), max_length=255,
        null=True, blank=True
    )
    requestor_name = models.CharField(
        verbose_name=_('requestor name'), max_length=255,
        null=True, blank=True
    )
    requestor_email = models.CharField(
        verbose_name=_('requestor email'), max_length=255,
        null=True, blank=True
    )

    class Meta:
        verbose_name = _('dref')
        verbose_name_plural = _('drefs')

    def save(self, *args, **kwargs):
        if self.date_of_approval:
            self.status = Dref.Status.COMPLETED
        elif not self.date_of_approval:
            self.status = Dref.Status.IN_PROGESS
        return super().save(*args, **kwargs)


class DrefCountryDistrict(models.Model):
    dref = models.ForeignKey(Dref, verbose_name=_('dref'),
                             on_delete=models.CASCADE)
    country = models.ForeignKey(Country, verbose_name=_('country'),
                                on_delete=models.CASCADE)
    district = models.ForeignKey(District, verbose_name=_('district'),
                                 blank=True, null=True,
                                 on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('country', 'district')
