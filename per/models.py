import reversion
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from api.models import Appeal, Country
from deployments.models import SectorTag
from main.fields import SecureFileField


class ProcessPhase(models.IntegerChoices):
    BASELINE = 0, _("baseline")
    ORIENTATION = 1, _("orientation")
    ASSESSMENT = 2, _("assessment")
    PRIORITIZATION = 3, _("prioritization")
    PLAN_OF_ACTION = 4, _("plan of action")
    ACTION_AND_ACCOUNTABILITY = 5, _("action and accountability")


@reversion.register()
class NSPhase(models.Model):
    """NS PER Process Phase"""

    # default=1 needed only for the migration, can be deleted later
    country = models.OneToOneField(Country, on_delete=models.CASCADE, default=1)
    phase = models.IntegerField(choices=ProcessPhase.choices, default=ProcessPhase.BASELINE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "updated_at",
            "country",
        )
        verbose_name = _("NS PER Process Phase")
        verbose_name_plural = _("NS-es PER Process Phase")

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        return "%s (%s)" % (name, self.phase)


# FIXME: should be removable in some way (?)
class Status(models.IntegerChoices):
    NO = 0, _("no")
    YES = 1, _("yes")
    NOT_REVIEWED = 2, _("not reviewed")
    DOES_NOT_EXIST = 3, _("does not exist")
    PARTIALLY_EXISTS = 4, _("partially exists")
    NEED_IMPROVEMENTS = 5, _("needs improvement")
    EXIST_COULD_BE_STRENGTHENED = 6, _("exists could be strengthened")
    HIGH_PERFORMANCE = 7, _("high performance")


# FIXME: can't remove because it's in the 0020 migration...
class Language(models.IntegerChoices):
    SPANISH = 0, _("spanish")
    FRENCH = 1, _("french")
    ENGLISH = 2, _("english")


@reversion.register()
class FormArea(models.Model):
    """PER Form Areas (top level)"""

    title = models.CharField(verbose_name=_("title"), max_length=250)
    area_num = models.IntegerField(verbose_name=_("area number"), default=1)

    def __str__(self):
        return f"Area {self.area_num} - {self.title}"


@reversion.register()
class FormComponentQuestionAndAnswer(models.Model):
    question = models.ForeignKey("FormQuestion", verbose_name=_("question"), null=True, blank=True, on_delete=models.SET_NULL)
    answer = models.ForeignKey("FormAnswer", verbose_name=_("answer"), null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(verbose_name=_("notes"), null=True, blank=True)


@reversion.register()
class FormComponent(models.Model):
    """PER Form Components inside Areas"""

    class FormComponentStatus(models.TextChoices):
        HIGH_PERFORMANCE = "high_performance", _("High Performance")
        EXISTS_COULD_BE_STRENGTHENED = "exists_could_be_strengthened", _("Exists – Could be Strengthened")
        NEEDS_IMPROVEMENT = "needs_improvement", _("Needs Improvement")
        PARTIALLY_EXISTS = "partially_exists", _("Partially Exists")
        DOES_NOT_EXIST = "does_not_exist", _("Does Not Exist")

    area = models.ForeignKey(FormArea, verbose_name=_("area"), on_delete=models.PROTECT)
    title = models.CharField(verbose_name=_("title"), max_length=250)
    component_num = models.IntegerField(verbose_name=_("component number"), default=1)
    component_letter = models.CharField(verbose_name=_("component letter"), max_length=3, null=True, blank=True)
    description = models.TextField(verbose_name=_("description"), null=True, blank=True)
    status = models.CharField(
        verbose_name=_("status"), max_length=100, choices=FormComponentStatus.choices, null=True, blank=True
    )
    question_responses = models.ManyToManyField(FormComponentQuestionAndAnswer, verbose_name=_("Question responses"), blank=True)
    is_parent = models.BooleanField(verbose_name=_("Is parent"), null=True, blank=True)
    has_question_group = models.BooleanField(verbose_name=_("Has Question Group"), null=True, blank=True)
    urban_considerations_guidance = HTMLField(verbose_name=_("Urban Considerations"), blank=True, default="")
    epi_considerations_guidance = HTMLField(verbose_name=_("EPI Considerations"), blank=True, default="")
    climate_environmental_considerations_guidance = HTMLField(
        verbose_name=_("Climate and Environmental Considerations "), blank=True, default=""
    )

    def __str__(self):
        return f"Component {self.component_num} - {self.title}"


class PerComponentRating(models.Model):
    title = models.CharField(verbose_name=_("title"), max_length=250)
    value = models.IntegerField(verbose_name=_("value"))

    def __str__(self):
        return f"{self.title} - {self.value}"


@reversion.register()
class FormComponentResponse(models.Model):
    component = models.ForeignKey(
        FormComponent,
        verbose_name=_("Form Component"),
        on_delete=models.CASCADE,
    )
    rating = models.ForeignKey(
        PerComponentRating,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    question_responses = models.ManyToManyField(FormComponentQuestionAndAnswer, verbose_name=_("Question responses"), blank=True)
    # consideration_responses fields
    urban_considerations = models.TextField(verbose_name=_("Urban Considerations"), null=True, blank=True)
    epi_considerations = models.TextField(verbose_name=_("Epi Considerations"), null=True, blank=True)
    climate_environmental_considerations = models.TextField(
        verbose_name=_("Climate Environmental Considerations"), null=True, blank=True
    )
    notes = models.TextField(verbose_name=_("Notes"), null=True, blank=True)


@reversion.register()
class AreaResponse(models.Model):
    area = models.ForeignKey(FormArea, verbose_name=_("Area"), on_delete=models.CASCADE)
    component_response = models.ManyToManyField(
        FormComponentResponse,
        verbose_name=_("Component Response"),
        blank=True,
    )


@reversion.register()
class PerAssessment(models.Model):
    overview = models.ForeignKey(
        "Overview",
        verbose_name="Overview",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL)
    area_responses = models.ManyToManyField(
        AreaResponse,
        verbose_name=_("Area Response"),
        blank=True,
    )
    is_draft = models.BooleanField(
        verbose_name=_("is draft"),
        default=True,
    )

    def __str__(self):
        return f"{self.overview.country.name} - {self.overview.assessment_number}"


@reversion.register()
class FormAnswer(models.Model):
    """PER Form answer possibilities"""

    text = models.CharField(verbose_name=_("text"), max_length=40)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.text


@reversion.register()
class FormQuestionGroup(models.Model):
    component = models.ForeignKey(FormComponent, verbose_name=_("component"), on_delete=models.PROTECT)
    title = models.CharField(verbose_name=_("title"), max_length=250)
    description = models.TextField(verbose_name=_("description"), null=True, blank=True)

    def __str__(self):
        return self.title


@reversion.register()
class FormQuestion(models.Model):
    """PER Form individual questions inside Components"""

    component = models.ForeignKey(FormComponent, verbose_name=_("component"), on_delete=models.PROTECT)
    question_group = models.ForeignKey(FormQuestionGroup, null=True, blank=True, on_delete=models.SET_NULL)
    question = models.CharField(verbose_name=_("question"), max_length=500)
    description = HTMLField(verbose_name=_("description"), null=True, blank=True)
    question_num = models.IntegerField(verbose_name=_("question number"), null=True, blank=True)
    answers = models.ManyToManyField(FormAnswer, verbose_name=_("answers"), blank=True)

    def __str__(self):
        return self.question


@reversion.register()
class FormPrioritizationComponent(models.Model):
    component = models.ForeignKey(FormComponent, verbose_name=_("component"), on_delete=models.CASCADE)
    is_prioritized = models.BooleanField(verbose_name=_("Is prioritized"), null=True, blank=True)
    justification_text = models.TextField(verbose_name=_("Justification Text"), null=True, blank=True)

    def __str__(self):
        return self.component.title


@reversion.register()
class FormPrioritization(models.Model):
    overview = models.ForeignKey("Overview", verbose_name=_("Overview"), null=True, blank=True, on_delete=models.PROTECT)
    prioritized_action_responses = models.ManyToManyField(
        FormPrioritizationComponent,
        verbose_name=_("Form prioritization component"),
        blank=True,
    )
    is_draft = models.BooleanField(
        verbose_name=_("is draft"),
        default=True,
    )

    def __str__(self):
        return str(self.overview)


# FIXME: can't remove because it's in the 0020 migration...
class CAssessmentType(models.IntegerChoices):
    SELF_ASSESSMENT = 0, _("self assessment")
    SIMULATION = 1, _("simulation")
    OPERATIONAL = 2, _("operational")
    POST_OPERATIONAL = 3, _("post operational")


@reversion.register()
class AssessmentType(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=200)

    class Meta:
        verbose_name = _("PER Assessment Type")
        verbose_name_plural = _("PER Assessment Types")

    def __str__(self):
        return self.name


@reversion.register()
class Overview(models.Model):
    class Phase(models.IntegerChoices):
        ORIENTATION = 1, _("Orientation")
        ASSESSMENT = 2, _("Assessment")
        PRIORITIZATION = 3, _("Prioritisation")
        WORKPLAN = 4, _("WorkPlan")
        ACTION_AND_ACCOUNTABILITY = 5, _("Action And Accountability")

    class AssessmentMethod(models.TextChoices):
        PER = "per", _("PER")
        DRCE = "drce", _("DRCE")
        WPNS = "wpns", _("WPNS")

    country = models.ForeignKey(
        Country, verbose_name=_("country"), related_name="per_overviews", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL)

    # Orientation
    date_of_orientation = models.DateField(verbose_name=_("Date of Orientation"), null=True, blank=True)
    orientation_documents = models.ManyToManyField(
        "PerFile",
        blank=True,
        verbose_name=_("orientation documents"),
    )

    # Assessment
    type_of_assessment = models.ForeignKey(
        AssessmentType,
        verbose_name=_("type of assessment"),
        related_name="type_of_assessment",
        null=True,
        on_delete=models.SET_NULL,
    )
    assessment_number = models.IntegerField(verbose_name=_("assessment number"), default=1)
    branches_involved = models.CharField(verbose_name=_("branches involved"), max_length=400, null=True, blank=True)
    date_of_assessment = models.DateField(verbose_name=_("date of assessment"), null=True, blank=True)
    assessment_method = models.CharField(
        verbose_name=_("what method has this assessment used"),
        max_length=90,
        null=True,
        blank=True,
        choices=AssessmentMethod.choices,
    )
    assess_preparedness_of_country = models.BooleanField(
        verbose_name=_("Do you want to assess the preparedness of your National Society for epidemics and pandemics?"),
        null=True,
        blank=True,
    )
    assess_urban_aspect_of_country = models.BooleanField(
        verbose_name=_("Do you want to assess the urban aspects of your National Society?"), null=True, blank=True
    )
    assess_climate_environment_of_country = models.BooleanField(
        verbose_name=_("Do you want to assess the climate and environment of your National Society?"), null=True, blank=True
    )

    # Previous PER Assessment
    date_of_previous_assessment = models.DateField(verbose_name=_("Date of previous assessment"), null=True, blank=True)
    type_of_previous_assessment = models.ForeignKey(
        AssessmentType,
        verbose_name=_("type of previous assessment"),
        related_name="type_of_previous_assessment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Workplan reviews planned
    workplan_development_date = models.DateField(verbose_name=_("Workplan Development Date"), null=True, blank=True)
    workplan_revision_date = models.DateField(verbose_name=_("Workplan Revision Date"), null=True, blank=True)

    # Contact Information
    facilitator_name = models.CharField(verbose_name=_("facilitator name"), max_length=90, null=True, blank=True)
    facilitator_email = models.CharField(verbose_name=_("facilitator email"), max_length=90, null=True, blank=True)
    facilitator_phone = models.CharField(verbose_name=_("facilitator phone"), max_length=90, null=True, blank=True)
    facilitator_contact = models.CharField(verbose_name=_("facilitator other contacts"), max_length=90, null=True, blank=True)
    ns_focal_point_name = models.CharField(verbose_name=_("ns focal point name"), max_length=90, null=True, blank=True)
    ns_focal_point_email = models.CharField(verbose_name=_("ns focal point email"), max_length=90, null=True, blank=True)
    ns_focal_point_phone = models.CharField(verbose_name=_("ns focal point phone"), max_length=90, null=True, blank=True)
    partner_focal_point_name = models.CharField(verbose_name=_("partner focal point name"), max_length=90, null=True, blank=True)
    partner_focal_point_email = models.CharField(
        verbose_name=_("partner focal point email"), max_length=90, null=True, blank=True
    )
    partner_focal_point_phone = models.CharField(
        verbose_name=_("partner focal point phone"), max_length=90, null=True, blank=True
    )
    partner_focal_point_organization = models.CharField(
        verbose_name=_("partner focal point organization name"), max_length=90, null=True, blank=True
    )
    ns_second_focal_point_name = models.CharField(
        verbose_name=_("ns second focal point name"), max_length=90, null=True, blank=True
    )
    ns_second_focal_point_email = models.CharField(
        verbose_name=_("ns second focal point email"), max_length=90, null=True, blank=True
    )
    ns_second_focal_point_phone = models.CharField(
        verbose_name=_("ns second focal point phone"), max_length=90, null=True, blank=True
    )

    # phase calculation
    phase = models.IntegerField(verbose_name=_("phase"), choices=Phase.choices, null=True, blank=True, default=Phase.ORIENTATION)

    # Added to track the draft overview
    is_draft = models.BooleanField(
        verbose_name=_("is draft"),
        default=True,
    )

    # Used to keep track of per export
    # exported_file = models.FileField(
    #     verbose_name=_('exported file'),
    #     upload_to='per/excel-export/',
    #     blank=True,
    #     null=True
    # )
    # exported_at = models.DateTimeField(
    #     verbose_name=_('exported at'),
    #     blank=True,
    #     null=True
    # )

    class Meta:
        ordering = ("country",)
        verbose_name = _("PER General Overview")
        verbose_name_plural = _("PER General Overviews")

    def get_included_forms(self):
        allForms = self.forms.all()
        return ", ".join(f"Area {form.area.area_num}" for form in allForms)

    def update_phase(self, new_phase: Phase, save_phase: bool = True):
        if self.phase != new_phase:
            self.phase = new_phase
            if save_phase:
                self.save(update_fields=("phase",))

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name or ""
        fpname = f" ({self.ns_focal_point_name})" if self.ns_focal_point_name else ""
        return f"{name}{fpname}"

    def save(self, *args, **kwargs):
        # get the latest
        if self.pk is None:
            overview = Overview.objects.filter(country=self.country).order_by("-assessment_number")
            if overview.exists():
                self.assessment_number = overview[0].assessment_number + 1
                self.date_of_previous_assessment = overview[0].date_of_assessment or None
                self.type_of_previous_assessment = overview[0].type_of_assessment or None
            else:
                self.assessment_number = 1
        super().save()


class PerFile(models.Model):
    file = SecureFileField(
        verbose_name=_("file"),
        upload_to="per/images/",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created_by"),
        on_delete=models.SET_NULL,
        null=True,
    )
    caption = models.CharField(max_length=225, blank=True, null=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _("per file")
        verbose_name_plural = _("per files")


@reversion.register()
class Form(models.Model):
    """Individually submitted PER Forms"""

    area = models.ForeignKey(FormArea, verbose_name=_("area"), null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL)
    overview = models.ForeignKey(Overview, verbose_name=_("overview"), related_name="forms", null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    comment = models.TextField(verbose_name=_("comment"), null=True, blank=True)  # form level comment

    class Meta:
        ordering = ("area", "created_at")
        verbose_name = _("Form")
        verbose_name_plural = _("Forms")

    def __str__(self):
        return f'{self.area} ({self.updated_at.strftime("%Y-%m-%d")})'


def question_details(question_id, code):
    q = code + question_id
    return q


@reversion.register()
class FormData(models.Model):
    """PER form data"""

    form = models.ForeignKey(Form, verbose_name=_("form"), related_name="form_data", on_delete=models.CASCADE)
    question = models.ForeignKey(FormQuestion, verbose_name=_("question"), null=True, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(FormAnswer, verbose_name=_("answer"), null=True, on_delete=models.CASCADE)
    notes = models.TextField(verbose_name=_("notes"), null=True, blank=True)

    class Meta:
        ordering = ("form", "question__question_num")
        verbose_name = _("Form Data")
        verbose_name_plural = _("Form Data")

    def __str__(self):
        if self.question:
            if self.question.component:
                return f"A{self.question.component.area.area_num} \
                         C{self.question.component.component_num} Q{self.question.question_num}"
            return f"Q{self.question.question_num}"
        return ""


class PriorityValue(models.IntegerChoices):
    LOW = 0, _("low")
    MID = 1, _("medium")
    HIGH = 2, _("high")


class WorkPlanStatus(models.IntegerChoices):
    STANDBY = 0, _("standby")
    ONGOING = 1, _("ongoing")
    CANCELLED = 2, _("cancelled")
    DELAYED = 3, _("delayed")
    PENDING = 4, _("pending")
    NEED_IMPROVEMENTS = 5, _("need improvements")
    FINISHED = 6, _("finished")
    APPROVED = 7, _("approved")
    CLOSED = 8, _("closed")


@reversion.register()
class WorkPlan(models.Model):
    prioritization = models.IntegerField(choices=PriorityValue.choices, default=0, verbose_name=_("prioritization"))
    components = models.CharField(verbose_name=_("components"), max_length=900, null=True, blank=True)
    benchmark = models.CharField(verbose_name=_("benchmark"), max_length=900, null=True, blank=True)
    actions = models.CharField(verbose_name=_("actions"), max_length=900, null=True, blank=True)
    comments = models.CharField(verbose_name=_("comments"), max_length=900, null=True, blank=True)
    timeline = models.DateTimeField(verbose_name=_("timeline"))
    status = models.IntegerField(choices=WorkPlanStatus.choices, default=0, verbose_name=_("status"))
    support_required = models.BooleanField(verbose_name=_("support required"), default=False)
    focal_point = models.CharField(verbose_name=_("focal point"), max_length=90, null=True, blank=True)
    country = models.ForeignKey(Country, verbose_name=_("country"), null=True, blank=True, on_delete=models.SET_NULL)
    code = models.CharField(verbose_name=_("code"), max_length=10, null=True, blank=True)
    question_id = models.CharField(verbose_name=_("question id"), max_length=10, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ("prioritization", "country")
        verbose_name = _("PER Work Plan")
        verbose_name_plural = _("PER Work Plans")

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        if self.question_id and self.code:
            verbose = question_details(self.question_id, self.code)
            if verbose and name:
                return "%s, %s" % (name, verbose)
        return "%s [%s %s]" % (name, self.code, self.question_id)


class Visibilities(models.IntegerChoices):
    HIDDEN = 0, _("hidden")
    VISIBLE = 1, _("visible")


def nice_document_path(instance, filename):
    return "perdocs/%s/%s" % (instance.country.id, filename)


@reversion.register()
class NiceDocument(models.Model):
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    name = models.CharField(verbose_name=_("name"), max_length=100)
    document = models.FileField(verbose_name=_("document"), null=True, blank=True, upload_to=nice_document_path)
    document_url = models.URLField(verbose_name=_("document url"), blank=True)
    country = models.ForeignKey(
        Country, verbose_name=_("country"), related_name="perdoc_country", null=True, blank=True, on_delete=models.SET_NULL
    )
    visibility = models.IntegerField(choices=Visibilities.choices, verbose_name=_("visibility"), default=Visibilities.VISIBLE)

    class Meta:
        ordering = ("visibility", "country")
        verbose_name = _("PER Document")
        verbose_name_plural = _("PER Documents")

    def __str__(self):
        return "%s - %s" % (self.country, self.name)


class PerWorkPlanStatus(models.IntegerChoices):
    NOT_STARTED = 0, _("Not Started")
    ONGOING = 1, _("Ongoing")
    DELAYED = 2, _("Delayed")
    STANDBY = 3, _("Standby")
    FINISHED = 4, _("Finished")


class PerWorkPlanComponent(models.Model):
    class SupportedByOrganizationType(models.IntegerChoices):
        UN_ORGANIZATION = 0, _("UN Organization")
        PRIVATE_SECTOR = 1, _("Private Sector")
        GOVERNMENT = 2, _("Government")
        NATIONAL_SOCIETY = 3, _("National Society")

    component = models.ForeignKey(
        FormComponent,
        verbose_name=_("Component"),
        on_delete=models.CASCADE,
    )
    actions = models.TextField(verbose_name=_("Actions"), max_length=900, null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    status = models.IntegerField(choices=PerWorkPlanStatus.choices, default=0, verbose_name=_("status"))
    supported_by = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    supported_by_organization_type = models.IntegerField(
        choices=SupportedByOrganizationType.choices,
        verbose_name=_("Supported By Organization Type"),
        null=True,
        blank=True,
    )


class CustomPerWorkPlanComponent(models.Model):
    actions = models.TextField(verbose_name=_("Actions"), max_length=900, null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    status = models.IntegerField(choices=PerWorkPlanStatus.choices, default=0, verbose_name=_("status"))
    supported_by = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    supported_by_organization_type = models.IntegerField(
        choices=PerWorkPlanComponent.SupportedByOrganizationType.choices,
        verbose_name=_("Supported By Organization Type"),
        null=True,
        blank=True,
    )


class PerWorkPlan(models.Model):
    overview = models.ForeignKey(Overview, verbose_name=_("Overview"), null=True, blank=True, on_delete=models.SET_NULL)
    prioritized_action_responses = models.ManyToManyField(
        PerWorkPlanComponent,
        verbose_name=_("WorkPlan Component"),
        blank=True,
    )
    additional_action_responses = models.ManyToManyField(
        CustomPerWorkPlanComponent,
        verbose_name=_("Custom Per-WorkPlan Component"),
        blank=True,
    )
    is_draft = models.BooleanField(
        verbose_name=_("is draft"),
        default=True,
    )

    def __str__(self):
        return f"{self.overview.id}"


@reversion.register()
class OrganizationTypes(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("title"))
    is_deprecated = models.BooleanField(default=False, help_text=_("Is this a deprecated Organization type?"))
    order = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Organization type")
        verbose_name_plural = _("Organization types")

    def __str__(self):
        return self.title


class LearningType(models.IntegerChoices):
    LESSON_LEARNED = 1, _("Lesson learned")
    CHALLENGE = 2, _("Challenge")


@reversion.register(
    follow=(
        "appeal_code",
        "organization",
        "sector",
        "per_component",
        "organization_validated",
        "sector_validated",
        "per_component_validated",
    )
)
class OpsLearning(models.Model):
    learning = models.TextField(verbose_name=_("learning"), null=True, blank=True)
    learning_validated = models.TextField(verbose_name=_("learning (validated)"), null=True, blank=True)
    appeal_code = models.ForeignKey(
        Appeal,
        to_field="code",
        db_column="appeal_code",
        verbose_name=_("appeal (MDR) code"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    appeal_document_id = models.IntegerField(verbose_name=_("Appeal document ID"), null=True, blank=True)
    type = models.IntegerField(verbose_name=_("type"), choices=LearningType.choices, default=LearningType.LESSON_LEARNED)
    type_validated = models.IntegerField(
        verbose_name=_("type (validated)"), choices=LearningType.choices, default=LearningType.LESSON_LEARNED
    )
    organization = models.ManyToManyField(
        OrganizationTypes, related_name="organizations", verbose_name=_("Organizations"), blank=True
    )
    organization_validated = models.ManyToManyField(
        OrganizationTypes, related_name="validated_organizations", verbose_name=_("Organizations (validated)"), blank=True
    )
    sector = models.ManyToManyField(SectorTag, related_name="sectors", verbose_name=_("Sectors"), blank=True)
    sector_validated = models.ManyToManyField(
        SectorTag, related_name="validated_sectors", verbose_name=_("Sectors (validated)"), blank=True
    )
    per_component = models.ManyToManyField(FormComponent, related_name="components", verbose_name=_("PER Components"), blank=True)
    per_component_validated = models.ManyToManyField(
        FormComponent, related_name="validated_components", verbose_name=_("PER Components (validated)"), blank=True
    )
    is_validated = models.BooleanField(verbose_name=_("is validated?"), default=False)
    modified_at = models.DateTimeField(verbose_name=_("modified_at"), auto_now=True)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)

    class Meta:
        ordering = ("learning",)
        verbose_name = _("Operational Learning")
        verbose_name_plural = _("Operational Learnings")

    def __str__(self):
        name = self.learning_validated if self.learning_validated else self.learning
        return "%s - %s" % (name, self.appeal_code) if self.appeal_code else name

    @staticmethod
    def is_user_admin(user):
        return (
            user is not None
            and not user.is_anonymous
            and user.is_superuser
            or user.groups.filter(name="OpsLearning Admin").exists()
        )

    # Is this really needed? The admin::save_model should be enough. FIXME
    def save(self, *args, **kwargs):
        if self.is_validated and self.id:
            if (
                self.learning_validated is None
                and self.type_validated == LearningType.LESSON_LEARNED.value
                and self.organization_validated.count() == 0
                and self.sector_validated.count() == 0
                and self.per_component_validated.count() == 0
            ):

                self.learning_validated = self.learning
                self.type_validated = self.type
                self.organization_validated.add(*[x[0] for x in self.organization.values_list()])
                self.sector_validated.add(*[x[0] for x in self.sector.values_list()])
                self.per_component_validated.add(*[x[0] for x in self.per_component.values_list()])

        return super(OpsLearning, self).save(*args, **kwargs)


class PerDocumentUpload(models.Model):
    file = SecureFileField(
        verbose_name=_("file"),
        upload_to="per/documents/",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created_by"),
        on_delete=models.SET_NULL,
        null=True,
    )
    country = models.ForeignKey(Country, verbose_name=_("country"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    per = models.ForeignKey(Overview, verbose_name=_("Per"), on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.country.name} - {self.created_by} - {self.per_id}"


class OpsLearningPromptResponseCache(models.Model):
    class PromptType(models.IntegerChoices):
        PRIMARY = 1, _("Primary")
        SECONDARY = 2, _("Secondary")

    prompt_hash = models.CharField(verbose_name=_("used prompt hash"), max_length=32)
    prompt = models.TextField(verbose_name=_("used prompt"), null=True, blank=True)
    type = models.IntegerField(verbose_name=_("type"), choices=PromptType.choices)

    response = models.JSONField(verbose_name=_("response"), default=dict)

    def __str__(self) -> str:
        return f"{self.type} - {self.prompt_hash}"


class OpsLearningCacheResponse(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, _("Pending")
        STARTED = 2, _("Started")
        SUCCESS = 3, _("Success")
        NO_EXTRACT_AVAILABLE = 4, _("No extract available")
        FAILED = 5, _("Failed")

    class ExportStatus(models.IntegerChoices):
        PENDING = 1, _("Pending")
        SUCCESS = 2, _("Success")
        FAILED = 3, _("Failed")

    used_filters_hash = models.CharField(verbose_name=_("used filters hash"), max_length=32)
    used_filters = models.JSONField(verbose_name=_("used filters"), default=dict)

    status = models.IntegerField(verbose_name=_("status"), choices=Status.choices, default=Status.PENDING)

    insights1_content = models.TextField(verbose_name=_("insights 1"), null=True, blank=True)
    insights2_content = models.TextField(verbose_name=_("insights 2"), null=True, blank=True)
    insights3_content = models.TextField(verbose_name=_("insights 3"), null=True, blank=True)

    insights1_title = models.CharField(verbose_name=_("insights 1 title"), max_length=255, null=True, blank=True)
    insights2_title = models.CharField(verbose_name=_("insights 2 title"), max_length=255, null=True, blank=True)
    insights3_title = models.CharField(verbose_name=_("insights 3 title"), max_length=255, null=True, blank=True)

    insights1_confidence_level = models.CharField(
        verbose_name=_("insights 1 confidence level"), max_length=10, null=True, blank=True
    )
    insights2_confidence_level = models.CharField(
        verbose_name=_("insights 2 confidence level"), max_length=10, null=True, blank=True
    )
    insights3_confidence_level = models.CharField(
        verbose_name=_("insights 3 confidence level"), max_length=10, null=True, blank=True
    )
    contradictory_reports = models.TextField(verbose_name=_("contradictory reports"), null=True, blank=True)

    used_ops_learning = models.ManyToManyField(
        OpsLearning,
        related_name="+",
    )
    modified_at = models.DateTimeField(verbose_name=_("modified_at"), auto_now=True)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)

    # Caching for the exported file
    export_status = models.IntegerField(
        verbose_name=_("export status"),
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
    )
    exported_file = models.FileField(
        verbose_name=_("exported file"), upload_to="ops-learning/summary/export/", blank=True, null=True
    )
    exported_at = models.DateTimeField(verbose_name=_("exported at"), blank=True, null=True)

    def __str__(self) -> str:
        return self.used_filters_hash


class OpsLearningSectorCacheResponse(models.Model):
    filter_response = models.ForeignKey(
        OpsLearningCacheResponse,
        verbose_name=_("filter response"),
        on_delete=models.CASCADE,
        related_name="ops_learning_sector",
    )
    sector = models.ForeignKey(
        SectorTag,
        verbose_name=_("sector"),
        on_delete=models.CASCADE,
        related_name="+",
    )
    content = models.TextField(verbose_name=_("content"), null=True, blank=True)
    used_ops_learning = models.ManyToManyField(
        OpsLearning,
        related_name="+",
    )

    def __str__(self) -> str:
        return f"Summary - sector - {self.sector.title}"


class OpsLearningComponentCacheResponse(models.Model):
    filter_response = models.ForeignKey(
        OpsLearningCacheResponse,
        verbose_name=_("filter response"),
        on_delete=models.CASCADE,
        related_name="ops_learning_component",
    )
    component = models.ForeignKey(
        FormComponent,
        verbose_name=_("component"),
        on_delete=models.CASCADE,
        related_name="+",
    )
    content = models.TextField(verbose_name=_("content"), null=True, blank=True)
    used_ops_learning = models.ManyToManyField(
        OpsLearning,
        related_name="+",
    )

    def __str__(self) -> str:
        return f"Summary - component - {self.component.title}"
