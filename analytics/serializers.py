from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import DocumentDownloadLog, DocumentSourceKey, DocumentTypeKey


class DocumentDownloadLogSerializer(serializers.ModelSerializer):
    # Accept known legacy/client source aliases and normalize them before save.
    SOURCE_ALIASES = {
        "/surge/catalogue/communication/too_long_string": "/surge/c/communication/1",
    }

    document_type = serializers.CharField()
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = DocumentDownloadLog
        fields = ("id", "document_type", "object_id", "url", "source")
        read_only_fields = ("id",)

    @staticmethod
    def _resolve_or_create_key(model, key: str):
        existing = model.objects.filter(key=key).first()
        if existing:
            return existing

        try:
            with transaction.atomic():
                return model.objects.create(key=key)
        except IntegrityError:
            # Another request may have created the same key concurrently.
            return model.objects.get(key=key)

    def validate_source(self, value):
        if value in (None, ""):
            return value

        normalized = self.SOURCE_ALIASES.get(value, value)
        return normalized.strip()

    def validate_document_type(self, value):
        normalized = value.strip() if isinstance(value, str) else value
        if not normalized:
            raise serializers.ValidationError('"document_type" cannot be empty.')
        return normalized

    def create(self, validated_data):
        document_type_key = validated_data.pop("document_type")
        source_key = validated_data.pop("source", None) or "other"

        document_type_obj = self._resolve_or_create_key(DocumentTypeKey, document_type_key)
        validated_data["document_type"] = document_type_obj

        source_obj = self._resolve_or_create_key(DocumentSourceKey, source_key)
        validated_data["source"] = source_obj

        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["document_type"] = instance.document_type.key
        data["source"] = instance.source.key if instance.source_id else None
        return data
