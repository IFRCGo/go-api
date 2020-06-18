from django.contrib import admin

from .models import (
    String,
)


@admin.register(String)
class StringAdmin(admin.ModelAdmin):
    search_fields = ('language', 'value',)
    list_display = ('key', 'language', 'value')
    list_filter = ('language',)
