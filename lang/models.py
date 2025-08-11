from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class String(models.Model):
    language = models.CharField(max_length=8, verbose_name=_("language"), choices=settings.LANGUAGES)
    key = models.CharField(max_length=255, verbose_name=_("key"))
    # Used by go-frontend translation management dashboard to detect changes.
    hash = models.CharField(max_length=32, null=True, blank=True, verbose_name=_("hash"))
    value = models.TextField(verbose_name=_("value"))
    page_name = models.CharField(max_length=255, verbose_name=_("Page name"), null=True, blank=True)

    class Meta:
        unique_together = ("language", "page_name", "key")
        verbose_name = _("String")
        verbose_name_plural = _("Strings")

    def __str__(self):
        return "{} ({})".format(self.value, self.language)

    @classmethod
    def _get_permission_per_language_codename(cls, lang_code):
        # NOTE: Make sure this is equivalent to the customly created permission code
        return f"{cls._meta.app_label}.lang__string__maintain__{lang_code}"

    @classmethod
    def has_perm(cls, user, lang_code):
        return user.has_perm(cls._get_permission_per_language_codename(lang_code))

    @classmethod
    def get_user_permissions_per_language(cls, user):
        return {
            lang_code: user.has_perm(cls._get_permission_per_language_codename(lang_code)) for lang_code, _ in settings.LANGUAGES
        }


class TranslationCache(models.Model):
    text = models.TextField()
    text_hash = models.CharField(max_length=64)
    source_language = models.CharField(max_length=16)
    dest_language = models.CharField(max_length=16)
    translated_text = models.TextField()
    table_field = models.CharField(max_length=128, blank=True, default="")  # for stats only
    other_fields = models.BooleanField(default=False)  # for stats only
    num_calls = models.IntegerField(default=0)  # for stats only
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("text", "source_language", "dest_language")
        indexes = [
            models.Index(fields=["text_hash", "source_language", "dest_language"]),
        ]

    def __str__(self):
        return f"{self.source_language}>{self.dest_language} – {self.table_field}: {self.text[:30]}..."
