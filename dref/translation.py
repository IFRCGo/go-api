from modeltranslation.translator import register, TranslationOptions

from dref.models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    PlannedInterventionIndicators,
    RiskSecurity,
)


@register(Dref)
class DrefTO(TranslationOptions):
    fields = (
        "title",
        "title_prefix",
        "event_text",
        "ns_request_text",
        "dref_recurrent_text",
        "lessons_learned",
        "event_description",
        "anticipatory_actions",
        "event_scope",
        "national_authorities",
        "ifrc",
        "icrc",
        "partner_national_society",
        "un_or_other_actor",
        "major_coordination_mechanism",
        "identified_gaps",
        "people_assisted",
        "selection_criteria",
        "operation_objective",
        "response_strategy",
        "human_resource",
        "surge_personnel_deployed",
        "logistic_capacity_of_ns",
        "pmer",
        "communication",
        "risk_security_concern",
    )


@register(DrefFile)
class DrefFileTO(TranslationOptions):
    fields = (
        "caption",
    )


@register(DrefFinalReport)
class DrefFinalReportTO(TranslationOptions):
    fields = (
        "title",
        "title_prefix",
        "event_description",
        "anticipatory_actions",
        "event_scope",
        "ifrc",
        "icrc",
        "partner_national_society",
        "national_authorities",
        "un_or_other_actor",
        "selection_criteria",
        "operation_objective",
        "response_strategy",
        "major_coordination_mechanism",
        "risk_security_concern",
        "event_text",
        "national_society_conducted_description",
        "financial_report_description",
    )


@register(DrefOperationalUpdate)
class DrefOperationalUpdateTO(TranslationOptions):
    fields = (
        "title",
        "title_prefix",
        "event_description",
        "anticipatory_actions",
        "event_scope",
        "ifrc",
        "icrc",
        "partner_national_society",
        "national_authorities",
        "un_or_other_actor",
        "major_coordination_mechanism",
        "people_assisted",
        "selection_criteria",
        "operation_objective",
        "response_strategy",
        "risk_security_concern",
        "anticipatory_to_response",
        "human_resource",
        "surge_personnel_deployed",
        "logistic_capacity_of_ns",
        "pmer",
        "communication",
    )


@register(IdentifiedNeed)
class IdentifiedNeedTO(TranslationOptions):
    fields = (
        "title",
        "description",
    )


@register(NationalSocietyAction)
class NationalSocietyActionTO(TranslationOptions):
    fields = (
        "description",
    )


@register(PlannedIntervention)
class PlannedInterventionTO(TranslationOptions):
    fields = (
        "title",
        "description",
        "progress_towards_outcome",
        "narrative_description_of_achievements",
        "challenges",
        "lessons_learnt",
    )


@register(PlannedInterventionIndicators)
class PlannedInterventionIndicatorsTO(TranslationOptions):
    fields = (
        "title",
    )


@register(RiskSecurity)
class RiskSecurityTO(TranslationOptions):
    fields = (
        "risk",
        "mitigation",
    )
