import uuid
from api.models import Country
from django.db import models
from django.conf import settings
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from tinymce import HTMLField
from deployments.models import ERUType
from api.storage import AzureStorage
from .questions_data import questions

# Write model properties to dictionary
def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values())
        else:
            data[f.name] = f.value_from_object(instance)
    return data

class ProcessPhase(IntEnum):
    BASELINE = 0
    ORIENTATION = 1
    ASSESSMENT = 2
    PRIORITIZATION = 3
    PLAN_OF_ACTION = 4
    ACTION_AND_ACCOUNTABILITY = 5

class NSPhase(models.Model):
    """ NS PER Process Phase """
    country = models.OneToOneField(Country, on_delete=models.CASCADE, default=1 ) #default=1 needed only for the migration, can be deleted later
    phase = EnumIntegerField(ProcessPhase, default=ProcessPhase.BASELINE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at', 'country', )
        verbose_name = 'NS PER Process Phase'
        verbose_name_plural = 'NS-es PER Process Phase'

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        return '%s (%s)' % (name, self.phase)

class Status(IntEnum):
    NO                          = 0
    YES                         = 1
    NOT_REVIEWED                = 2 # Not Reviewed     
    DOES_NOT_EXIST              = 3 # Does not exist
    PARTIALLY_EXISTS            = 4 # Partially exists
    NEED_IMPROVEMENTS           = 5 # Need improvements
    EXIST_COULD_BE_STRENGTHENED = 6 # Exist, could be strengthened
    HIGH_PERFORMANCE            = 7 # High Performance

class Language(IntEnum):
    SPANISH = 0
    FRENCH =  1
    ENGLISH = 2

class Draft(models.Model):
    """ PER draft form header """
    code = models.CharField(max_length=10)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    data = models.TextField(null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ('code', 'created_at')
        verbose_name = 'Draft Form'
        verbose_name_plural = 'Draft Forms'

    def __str__(self):
        if self.country is None:
            country = None
        else:
            country = self.country.society_name
        return '%s - %s (%s)' % (self.code, self.user, country)

class Form(models.Model):
    """ PER form header """
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    language = EnumIntegerField(Language)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    ns = models.CharField(max_length=100, null=True, blank=True) # redundant, because country has defined ns – later in "more ns/country" case it can be useful.
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(default=timezone.now)
    finalized = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(default='192.168.0.1')
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    comment = models.TextField(null=True, blank=True) # form level comment

    class Meta:
        ordering = ('code', 'name', 'language', 'created_at')
        verbose_name = 'Form'
        verbose_name_plural = 'Forms'

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        return '%s - %s (%s, %s)' % (self.code, self.name, self.language, name)

def question_details(question_id, code):
    q = code + question_id
    return questions.get(q, '')

class FormData(models.Model):
    """ PER form data """
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    question_id = models.CharField(max_length=10)
    selected_option = EnumIntegerField(Status)
    notes = models.TextField()

    class Meta:
        ordering = ('form', 'question_id')
        verbose_name = 'Form Data'
        verbose_name_plural = 'Form Data'

    def __str__(self):

        #return '%s / %s' % (self.question_id, self.form)
        return question_details(self.question_id, self.form.code)

class PriorityValue(IntEnum):
    LOW  = 0
    MID  = 1
    HIGH = 2

class WorkPlanStatus(IntEnum):
    STANDBY            = 0
    ONGOING            = 1
    CANCELLED          = 2
    DELAYED            = 3
    PENDING            = 4
    NEED_IMPROVEMENTS  = 5
    FINISHED           = 6
    APPROVED           = 7
    CLOSED             = 8

class WorkPlan(models.Model):
    prioritization = EnumIntegerField(PriorityValue)
    components = models.CharField(max_length=900,null=True, blank=True)
    benchmark = models.CharField(max_length=900,null=True, blank=True)
    actions = models.CharField(max_length=900,null=True, blank=True)
    comments = models.CharField(max_length=900,null=True, blank=True)
    timeline = models.DateTimeField()
    status = EnumIntegerField(WorkPlanStatus)
    support_required = models.BooleanField(default=False)
    focal_point = models.CharField(max_length=90,null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    code = models.CharField(max_length=10, null=True, blank=True)
    question_id = models.CharField(max_length=10, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('prioritization', 'country')
        verbose_name = 'PER Work Plan'
        verbose_name_plural = 'PER Work Plans'

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        if self.question_id and self.code:
            verbose = question_details(self.question_id, self.code)
            if verbose and name:
                return '%s, %s' % (name, verbose)
        return '%s [%s %s]' % (name, self.code, self.question_id)

class CAssessmentType(IntEnum):
    SELF_ASSESSMENT  = 0
    SIMULATION       = 1
    OPERATIONAL      = 2
    POST_OPERATIONAL = 3

class Overview(models.Model):
    # Without related_name Django gives: Reverse query name for 'Overview.country' clashes with field name 'Country.overview'.
    country = models.ForeignKey(Country, related_name='asmt_country', null=True, blank=True, on_delete=models.SET_NULL)
    # national_society = models.CharField(max_length=90,null=True, blank=True) Redundant
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    date_of_current_capacity_assessment = models.DateTimeField()
    type_of_capacity_assessment = EnumIntegerField(CAssessmentType, default=CAssessmentType.SELF_ASSESSMENT)
    date_of_last_capacity_assessment = models.DateTimeField(null=True, blank=True)
    type_of_last_capacity_assessment = EnumIntegerField(CAssessmentType, default=CAssessmentType.SELF_ASSESSMENT)
    branch_involved = models.CharField(max_length=90,null=True, blank=True)
    focal_point_name = models.CharField(max_length=90,null=True, blank=True)
    focal_point_email = models.CharField(max_length=90,null=True, blank=True)
    had_previous_assessment = models.BooleanField(default=False)
    focus = models.CharField(max_length=90,null=True, blank=True)
    facilitated_by = models.CharField(max_length=90,null=True, blank=True)
    facilitator_email = models.CharField(max_length=90,null=True, blank=True)
    phone_number = models.CharField(max_length=90,null=True, blank=True)
    skype_address = models.CharField(max_length=90,null=True, blank=True)
    date_of_mid_term_review = models.DateTimeField()
    approximate_date_next_capacity_assmt = models.DateTimeField()

    class Meta:
        ordering = ('country',)
        verbose_name = 'PER General Overview'
        verbose_name_plural = 'PER General Overviews'

    def __str__(self):
        if self.country is None:
            name = None
        else:
            name = self.country.society_name
        return '%s (%s)' % (name, self.focal_point_name)

class Visibilities(IntEnum):
    HIDDEN = 0
    VISIBLE = 1


def nice_document_path(instance, filename):
    return 'perdocs/%s/%s' % (instance.country.id, filename)


class NiceDocument(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    document = models.FileField(null=True, blank=True, upload_to=nice_document_path, storage=AzureStorage())
    document_url = models.URLField(blank=True)
    country = models.ForeignKey(Country, related_name='perdoc_country', null=True, blank=True, on_delete=models.SET_NULL)
    visibility = EnumIntegerField(Visibilities, default=Visibilities.VISIBLE)

    class Meta:
        ordering = ('visibility', 'country')
        verbose_name = 'PER Document'
        verbose_name_plural = 'PER Documents'

    def __str__(self):
        return '%s - %s' % (self.country, self.name)

