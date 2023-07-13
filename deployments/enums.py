from . import models

enum_register = {
    'eru_type': models.ERUType,
    'personnel_type': models.Personnel.TypeChoices,
    'personnle_molnix_status': models.Personnel.StatusChoices,
    'project_programme_type': models.ProgrammeTypes,
    'project_status': models.Statuses,
    'project_operation_type': models.OperationTypes,
    'emergency_project_activity_lead': models.EmergencyProject.ActivityLead,
    'emergency_project_status': models.EmergencyProject.ActivityStatus,
    'emergency_project_activity_people_households': models.EmergencyProjectActivity.PeopleHouseholds,
}