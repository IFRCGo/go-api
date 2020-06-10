from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import models


class Language(models.Model):
    """
    Language is used to store go-frontend language framework data
    """
    code = models.CharField(max_length=255, unique=True, choices=settings.LANGUAGES)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

    def __str__(self):
        return self.code

    def clean(self):
        self.code = self.code.lower()


class String(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    # Used by go-frontend translation management dashboard to detect changes.
    hash = models.CharField(max_length=32, null=True, blank=True)
    value = models.TextField()

    class Meta:
        unique_together = ('language', 'key')
        verbose_name = _('String')
        verbose_name_plural = _('Strings')

    def __str__(self):
        return '{} ({})'.format(self.value, self.language.code)
