from django.contrib import admin

# Register your models here.
from .models import (
    Language,
    String,
)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('code', 'description')


@admin.register(String)
class StringAdmin(admin.ModelAdmin):
    search_fields = ('language', 'value',)
    list_display = ('key', 'language', 'value')
    list_filter = ('language',)
