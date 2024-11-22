from . import models

enum_register = {
    "workplanstatus": models.PerWorkPlanStatus,
    "perphases": models.Overview.Phase,
    "overviewassessmentmethods": models.Overview.AssessmentMethod,
    "component_status": models.FormComponent.FormComponentStatus,
    "supported_by_organization_type": models.PerWorkPlanComponent.SupportedByOrganizationType,
    "learning_type": models.LearningType,
}
