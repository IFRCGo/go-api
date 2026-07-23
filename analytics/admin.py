from django.contrib import admin

from .models import DocumentDownloadLog, DocumentSourceKey, DocumentTypeKey


@admin.register(DocumentDownloadLog)
class DocumentDownloadLogAdmin(admin.ModelAdmin):
    list_display = ("downloaded_at", "document_type", "source", "url_abbrev", "object_id", "user", "ip_address")
    list_filter = ("document_type", "source")
    date_hierarchy = "downloaded_at"
    search_fields = ("url", "user__username", "user__email")
    readonly_fields = (
        "document_type",
        "object_id",
        "url",
        "source",
        "user",
        "downloaded_at",
        "ip_address",
    )
    ordering = ("-downloaded_at",)

    @admin.display(description="URL-abbrev", ordering="url")
    def url_abbrev(self, obj):
        if not obj.url:
            return ""

        # Keep the first 22 chars after the protocol slashes and the last 10 chars.
        url_parts = obj.url.split("//", 1)
        after_second_slash = url_parts[1] if len(url_parts) > 1 else obj.url
        return f"{after_second_slash[:22]}...{obj.url[-10:]}"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DocumentTypeKey)
class DocumentTypeKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "key")
    search_fields = ("key",)
    ordering = ("key",)


@admin.register(DocumentSourceKey)
class DocumentSourceKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "key")
    search_fields = ("key",)
    ordering = ("key",)
