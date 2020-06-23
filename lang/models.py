from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models


class String(models.Model):
    language = models.CharField(max_length=8, verbose_name=_('language'), choices=settings.LANGUAGES)
    key = models.CharField(max_length=255, verbose_name=_('key'))
    # Used by go-frontend translation management dashboard to detect changes.
    hash = models.CharField(max_length=32, null=True, blank=True, verbose_name=_('hash'))
    value = models.TextField(verbose_name=_('value'))

    class Meta:
        unique_together = ('language', 'key')
        verbose_name = _('String')
        verbose_name_plural = _('Strings')

    def __str__(self):
        return '{} ({})'.format(self.value, self.language)
