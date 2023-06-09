import reversion
from api.models import Country
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from tinymce import HTMLField


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
class FormComponentConsiderations(models.Model):
    urban_considerations = models.TextField(
        verbose_name=_("Urban Considerations"),
        null=True, blank=True
    )
    epi_considerations = models.TextField(
        verbose_name=_("Epi Considerations"),
        null=True, blank=True
    )
    climate_environmental_conisderations = models.TextField(
        verbose_name=_("Climate Environmental Considerations"),
        null=True, blank=True
    )


@reversion.register()
class FormComponentQuestionAndAnswer(models.Model):
    question = models.ForeignKey(
        "FormQuestion", verbose_name=_("question"),
        null=True, on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        "FormAnswer", verbose_name=_("answer"),
        null=True, on_delete=models.CASCADE
    )
    notes = models.TextField(
        verbose_name=_("notes"),
        null=True, blank=True
    )


@reversion.register()
class FormComponent(models.Model):
    """PER Form Components inside Areas"""

    class FormComponentStatus(models.TextChoices):
        HIGH_PERFORMANCE = "high_performance", _("High Performance")
        EXISTS_COULD_BE_STRENGTHENED = "exists_could_be_strengthened", _("Exits Could be Strengthened")
        NEEDS_IMPROVEMENT = "needs_improvement", _("Needs Improvement")
        PARTIALLY_EXISTS = "partially_exists", _("Partially Exists")
        DOES_NOT_EXIST = "does_not_exist", _("Does Not Exist")

    area = models.ForeignKey(FormArea, verbose_name=_("area"), on_delete=models.PROTECT)
    title = models.CharField(verbose_name=_("title"), max_length=250)
    component_num = models.IntegerField(verbose_name=_("component number"), default=1)
    component_letter = models.CharField(verbose_name=_("component letter"), max_length=3, null=True, blank=True)
    description = models.TextField(verbose_name=_("description"), null=True, blank=True)
    status = models.CharField(
        verbose_name=_("status"), max_length=100,
        choices=FormComponentStatus.choices, null=True, blank=True
    )
    consideration_responses = models.ManyToManyField(
        FormComponentConsiderations,
        verbose_name=_("Consideration responses"),
        blank=True
    )
    question_responses = models.ManyToManyField(
        FormComponentQuestionAndAnswer,
        verbose_name=_("Question responses"),
        blank=True
    )

    def __str__(self):
        return f"Component {self.component_num} - {self.title}"


@reversion.register()
class FormComponentResponse(models.Model):

    class FormComponentStatus(models.TextChoices):
        HIGH_PERFORMANCE = "high_performance", _("High Performance")
        EXISTS_COULD_BE_STRENGTHENED = "exists_could_be_strengthened", _("Exits Could be Strengthened")
        NEEDS_IMPROVEMENT = "needs_improvement", _("Needs Improvement")
        PARTIALLY_EXISTS = "partially_exists", _("Partially Exists")
        DOES_NOT_EXIST = "does_not_exist", _("Does Not Exist")

    component = models.ForeignKey(
        FormComponent,
        verbose_name=_("Form Component"),
        on_delete=models.PROTECT,
        blank=True, null=True,
    )
    status = models.CharField(
        verbose_name=_("status"), max_length=100,
        choices=FormComponentStatus.choices, null=True, blank=True
    )
    consideration_responses = models.ManyToManyField(
        FormComponentConsiderations,
        verbose_name=_("Consideration responses"),
        blank=True
    )
    question_responses = models.ManyToManyField(
        FormComponentQuestionAndAnswer,
        verbose_name=_("Question responses"),
        blank=True
    )


@reversion.register()
class AreaResponse(models.Model):
    area = models.ForeignKey(
        FormArea,
        verbose_name=_("Area"),
        on_delete=models.CASCADE
    )
    component_response = models.ManyToManyField(
        FormComponentResponse,
        verbose_name=_("Component Response"),
        blank=True,
    )
    is_draft = models.BooleanField(
        verbose_name=_("is draft"),
        null=True, blank=True
    )


@reversion.register()
class PerAssessment(models.Model):
    overview = models.ForeignKey(
        "Overview",
        verbose_name="Overview",
        on_delete=models.PROTECT,
        blank=True, null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"),
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    area_responses = models.ManyToManyField(
        AreaResponse,
        verbose_name=_("Area Response"),
        blank=True,
    )

    def __str__(self):
        return f'{self.overview.country.name} - {self.overview.assessment_number}'


@reversion.register()
class FormAnswer(models.Model):
    """PER Form answer possibilities"""

    text = models.CharField(verbose_name=_("text"), max_length=40)

    def __str__(self):
        return self.text


@reversion.register()
class FormQuestion(models.Model):
    """PER Form individual questions inside Components"""

    component = models.ForeignKey(FormComponent, verbose_name=_("component"), on_delete=models.PROTECT)
    question = models.CharField(verbose_name=_("question"), max_length=500)
    description = HTMLField(verbose_name=_("description"), null=True, blank=True)
    question_num = models.IntegerField(verbose_name=_("question number"), null=True, blank=True)
    answers = models.ManyToManyField(FormAnswer, verbose_name=_("answers"), blank=True)
    is_epi = models.BooleanField(verbose_name=_("is epi"), default=False)
    is_benchmark = models.BooleanField(verbose_name=_("is benchmark"), default=False)
    # NOTE: What about the status field????

    def __str__(self):
        return self.question


@reversion.register()
class FormPrioritizationComponent(models.Model):
    component = models.ForeignKey(FormComponent, verbose_name=_("component"), on_delete=models.PROTECT, null=True, blank=True)
    is_prioritized = models.BooleanField(verbose_name=_("Is prioritized"), null=True, blank=True)
    justification_text = models.TextField(verbose_name=_("Justification Text"), null=True, blank=True)

    def __str__(self):
        return self.component.title


@reversion.register()
class FormPrioritization(models.Model):
    overview = models.ForeignKey("Overview", verbose_name=_("Overview"), null=True, blank=True, on_delete=models.PROTECT)
    component_responses = models.ManyToManyField(
        FormPrioritizationComponent,
        verbose_name=_("Form prioritization component"),
        blank=True,
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
    country = models.ForeignKey(
        Country, verbose_name=_("country"),
        related_name="per_overviews",
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL
    )

    # Orientation
    date_of_orientation = models.DateField(verbose_name=_("Date of Orientation"), null=True, blank=True)
    orientation_document = models.FileField(
        verbose_name=_("Orientation Document"), null=True, blank=True, upload_to="per/documents/"
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
    date_of_assessment = models.DateField(verbose_name=_("date of assessment"))
    method_asmt_used = models.CharField(
        verbose_name=_("what method has this assessment used"), max_length=90, null=True, blank=True
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

    # Previouse PER Assessment
    date_of_previous_assessment = models.DateField(verbose_name=_("Date of previous assessment"), null=True, blank=True)
    type_of_per_assessment = models.CharField(
        verbose_name=_("Type of Per Asessement"), max_length=255, null=True, blank=True
    )
    # Reviews Planned
    date_of_mid_term_review = models.DateField(
        verbose_name=_("estimated date of mid term review"), null=True, blank=True
    )
    date_of_next_asmt = models.DateField(verbose_name=_("estimated date of next assessment"), null=True, blank=True)

    # Workplan reviews planned
    workplan_development_date = models.DateField(
        verbose_name=_("Workplan Development Date"),
        null=True, blank=True
    )
    workplan_revision_date = models.DateField(
        verbose_name=_("Workplan Revision Date"),
        null=True, blank=True
    )

    # Contact Information
    facilitator_name = models.CharField(verbose_name=_("facilitator name"), max_length=90, null=True, blank=True)
    facilitator_email = models.CharField(verbose_name=_("facilitator email"), max_length=90, null=True, blank=True)
    facilitator_phone = models.CharField(verbose_name=_("facilitator phone"), max_length=90, null=True, blank=True)
    facilitator_contact = models.CharField(
        verbose_name=_("facilitator other contacts"), max_length=90, null=True, blank=True
    )
    ns_focal_point_name = models.CharField(verbose_name=_("ns focal point name"), max_length=90, null=True, blank=True)
    ns_focal_point_email = models.CharField(verbose_name=_("ns focal point email"), max_length=90, null=True, blank=True)
    ns_focal_point_phone = models.CharField(verbose_name=_("ns focal point phone"), max_length=90, null=True, blank=True)
    partner_focal_point_name = models.CharField(
        verbose_name=_("partner focal point name"), max_length=90, null=True, blank=True
    )
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
        verbose_name=_("ns second focal point name"),
        max_length=90, null=True, blank=True
    )
    ns_second_focal_point_email = models.CharField(
        verbose_name=_("ns second focal point email"),
        max_length=90, null=True, blank=True
    )
    ns_second_focal_point_phone = models.CharField(
        verbose_name=_("ns second focal point phone"),
        max_length=90, null=True, blank=True
    )

    # Misc
    is_epi = models.BooleanField(verbose_name=_("is epi"), default=False)
    is_finalized = models.BooleanField(verbose_name=_("is finalized"), default=False)
    other_consideration = models.CharField(
        verbose_name=_("other consideration"),
        max_length=400,
        null=True, blank=True
    )

    class Meta:
        ordering = ("country",)
        verbose_name = _("PER General Overview")
        verbose_name_plural = _("PER General Overviews")

    def get_included_forms(self):
        allForms = self.forms.all()
        return ", ".join(f"Area {form.area.area_num}" for form in allForms)

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name or ""
        fpname = f" ({self.ns_focal_point_name})" if self.ns_focal_point_name else ""
        return f"{name}{fpname}"

    def save(self, *args, **kwargs):
        super().save()
        # get the latest
        if self.pk is None:
            overview = Overview.objects.filter(country=self.country).order_by('-assessment_number')
            if overview.exists():
                self.assessment_number = overview[0].assessment_number + 1


@reversion.register()
class Form(models.Model):
    """Individually submitted PER Forms"""

    area = models.ForeignKey(FormArea, verbose_name=_("area"), null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL
    )
    overview = models.ForeignKey(
        Overview, verbose_name=_("overview"), related_name="forms", null=True, on_delete=models.CASCADE
    )
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), null=True, blank=True, on_delete=models.SET_NULL
    )

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
    visibility = models.IntegerField(
        choices=Visibilities.choices, verbose_name=_("visibility"), default=Visibilities.VISIBLE
    )

    class Meta:
        ordering = ("visibility", "country")
        verbose_name = _("PER Document")
        verbose_name_plural = _("PER Documents")

    def __str__(self):
        return "%s - %s" % (self.country, self.name)


class PerWorkPlanComponent(models.Model):
    component = models.ForeignKey(
        FormComponent, verbose_name=_("Component"), on_delete=models.PROTECT, null=True, blank=True
    )
    actions = models.TextField(verbose_name=_("Actions"), max_length=900, null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    status = models.IntegerField(choices=WorkPlanStatus.choices, default=0, verbose_name=_("status"))


class CustomPerWorkPlanComponent(models.Model):
    actions = models.TextField(verbose_name=_("Actions"), max_length=900, null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    status = models.IntegerField(choices=WorkPlanStatus.choices, default=0, verbose_name=_("status"))


class PerWorkPlan(models.Model):
    overview = models.ForeignKey(Overview, verbose_name=_("Overview"), null=True, blank=True, on_delete=models.SET_NULL)
    component_responses = models.ManyToManyField(
        PerWorkPlanComponent,
        verbose_name=_("WorkPlan Component"),
        blank=True,
    )
    custom_component_responses = models.ManyToManyField(
        CustomPerWorkPlanComponent,
        verbose_name=_("Custom Per-WorkPlan Component"),
        blank=True,
    )

    def __str__(self):
        return f"{self.overview.id}"
