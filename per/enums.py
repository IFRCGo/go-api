from . import models

enum_register = {
    'workplanstatus': models.WorkPlanStatus,
    'perphases': models.Overview.Phase,
    'overviewassessmentmethods': models.Overview.AssessmentMethod
}
