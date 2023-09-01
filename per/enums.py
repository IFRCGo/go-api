from . import models

enum_register = {
    'workplanstatus': models.PerWorkPlanStaus,
    'perphases': models.Overview.Phase,
    'overviewassessmentmethods': models.Overview.AssessmentMethod,
    'component_status': models.FormComponent.FormComponentStatus
}