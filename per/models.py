import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from tinymce import HTMLField

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

class Form(models.Model):
    """ PER form header """
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    language = EnumIntegerField(Language)
    user = models.CharField(max_length=100, null=True, blank=True) #later maybe models.ForeignKey(RealUser, null=True)
    ns = models.CharField(max_length=100, null=True, blank=True) #later maybe models.ForeignKey(NationalSociety, null=True)
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

    def __str__(self):
        return '%s - %s (%s)' % (self.code, self.name, self.language)

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
        return self.name
