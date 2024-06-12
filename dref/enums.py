from . import models

enum_register = {
    "national_society_action_title": models.NationalSocietyAction.Title,
    "identified_need_title": models.IdentifiedNeed.Title,
    "planned_intervention_title": models.PlannedIntervention.Title,
    "dref_dref_type": models.Dref.DrefType,
    "dref_onset_type": models.Dref.OnsetType,
    "dref_disaster_category": models.Dref.DisasterCategory,
    "dref_status": models.Dref.Status,
}
