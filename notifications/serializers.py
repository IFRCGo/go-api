from rest_framework import serializers

from api.serializers import (
    MiniCountrySerializer,
    MiniEventSerializer,
    SurgeEventSerializer,
)
from deployments.serializers import MolnixTagSerializer
from lang.serializers import ModelSerializer

from .models import Subscription, SurgeAlert


class SurgeAlertSerializer(ModelSerializer):
    event = SurgeEventSerializer(required=False)
    country = MiniCountrySerializer(required=False)
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    molnix_status_display = serializers.CharField(source="get_molnix_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = SurgeAlert
        fields = (
            "operation",
            "country",
            "message",
            "deployment_needed",
            "is_private",
            "event",
            "created_at",
            "id",
            "atype",
            "atype_display",
            "category",
            "category_display",
            "molnix_id",
            "molnix_tags",
            "molnix_status",
            "opens",
            "closes",
            "start",
            "end",
            "molnix_status",
            "molnix_status_display",
        )


class SurgeAlertCsvSerializer(ModelSerializer):
    """CSV-friendly serializer with flattened fields for consistent column count across pages"""

    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    molnix_status_display = serializers.CharField(source="get_molnix_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    # Flattened country fields
    country_id = serializers.IntegerField(source="country.id", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)
    country_iso = serializers.CharField(source="country.iso", read_only=True)
    country_iso3 = serializers.CharField(source="country.iso3", read_only=True)
    country_society_name = serializers.CharField(source="country.society_name", read_only=True)
    country_region = serializers.IntegerField(source="country.region.id", read_only=True)

    # Flattened event fields
    event_id = serializers.IntegerField(source="event.id", read_only=True)
    event_name = serializers.CharField(source="event.name", read_only=True)
    event_dtype_id = serializers.IntegerField(source="event.dtype.id", read_only=True)
    event_dtype_name = serializers.CharField(source="event.dtype.name", read_only=True)
    event_glide = serializers.CharField(source="event.glide", read_only=True)
    event_disaster_start_date = serializers.DateTimeField(source="event.disaster_start_date", read_only=True)
    event_auto_generated = serializers.BooleanField(source="event.auto_generated", read_only=True)
    event_ifrc_severity_level = serializers.IntegerField(source="event.ifrc_severity_level", read_only=True)
    event_num_affected = serializers.IntegerField(source="event.num_affected", read_only=True)
    event_parent_event = serializers.IntegerField(source="event.parent_event.id", read_only=True)
    event_summary = serializers.SerializerMethodField()
    event_tab_one_title = serializers.CharField(source="event.tab_one_title", read_only=True)
    event_tab_two_title = serializers.CharField(source="event.tab_two_title", read_only=True)
    event_tab_three_title = serializers.CharField(source="event.tab_three_title", read_only=True)
    event_translation_module_original_language = serializers.CharField(
        source="event.translation_module_original_language", read_only=True
    )
    event_updated_at = serializers.DateTimeField(source="event.updated_at", read_only=True)

    # Comma-separated lists for many-to-many relationships
    event_countries = serializers.SerializerMethodField()
    event_appeals = serializers.SerializerMethodField()
    molnix_tags_names = serializers.SerializerMethodField()
    molnix_tags_ids = serializers.SerializerMethodField()
    molnix_tags_types = serializers.SerializerMethodField()

    class Meta:
        model = SurgeAlert
        fields = (
            "id",
            "molnix_id",
            "created_at",
            "operation",
            "message",
            "deployment_needed",
            "is_private",
            "atype",
            "atype_display",
            "category",
            "category_display",
            "molnix_status",
            "molnix_status_display",
            "opens",
            "closes",
            "start",
            "end",
            # Country fields (flattened)
            "country_id",
            "country_name",
            "country_iso",
            "country_iso3",
            "country_society_name",
            "country_region",
            # Event fields (flattened)
            "event_id",
            "event_name",
            "event_dtype_id",
            "event_dtype_name",
            "event_glide",
            "event_disaster_start_date",
            "event_auto_generated",
            "event_ifrc_severity_level",
            "event_num_affected",
            "event_parent_event",
            "event_summary",
            "event_tab_one_title",
            "event_tab_two_title",
            "event_tab_three_title",
            "event_translation_module_original_language",
            "event_updated_at",
            "event_countries",
            "event_appeals",
            # Molnix tags (comma-separated)
            "molnix_tags_names",
            "molnix_tags_ids",
            "molnix_tags_types",
        )

    @staticmethod
    def get_event_summary(obj):
        """Return HTML-stripped first 300 characters of event summary with empty lines removed"""
        if obj.event and obj.event.summary:
            import re
            from html import unescape

            text = obj.event.summary

            # Remove Microsoft Office table styles and metadata (before HTML stripping)
            # Match content between /* Style Definitions */ and the closing brace
            text = re.sub(r"/\*\s*Style Definitions\s*\*/.*?}", "", text, flags=re.DOTALL)
            # Remove other common MS Office artifacts
            text = re.sub(r"Normal\s+0\s+\d+\s+false\s+false\s+false\s+[A-Z-]+(?:\s+[A-Z-]+)*", "", text)
            text = re.sub(r"table\.MsoNormalTable\s*{[^}]*}", "", text, flags=re.DOTALL)

            # Strip HTML tags
            text = re.sub(r"<[^>]+>", "", text)
            # Decode HTML entities (&eacute; -> é, etc.)
            text = unescape(text)
            # Remove lines that contain only whitespace or are empty
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            # Remove lines that only contain "DISASTER OVERVIEW" or "Summary"
            lines = [line for line in lines if line.strip().upper() != "DISASTER OVERVIEW" and line.strip().upper() != "SUMMARY"]
            # Join remaining lines with newline
            text = "\n".join(lines)
            # Return first 300 characters
            return text[:300]
        return ""

    @staticmethod
    def get_event_countries(obj):
        """Return structured list of countries with name, fdrs, iso, iso3 (separated by |)"""
        if obj.event and obj.event.countries.exists():
            country_data = []
            for country in obj.event.countries.all():
                # Format: name;fdrs;iso;iso3
                parts = [country.name or "", country.fdrs or "", country.iso or "", country.iso3 or ""]
                country_data.append(";".join(parts))
            return " | ".join(country_data)
        return ""

    @staticmethod
    def get_event_appeals(obj):
        """Return structured list of appeals with all details (separated by |)
        in a format code;amount_funded;amount_requested;atype;atype_display;start_date;end_date;
        num_beneficiaries;sector;status_display
        """
        if obj.event:
            appeals = obj.event.appeals.all()
            if appeals:
                appeal_data = []
                for appeal in appeals:
                    parts = [
                        appeal.code or "",
                        str(appeal.amount_funded) if appeal.amount_funded is not None else "",
                        str(appeal.amount_requested) if appeal.amount_requested is not None else "",
                        str(appeal.atype) if appeal.atype is not None else "",
                        appeal.get_atype_display() if hasattr(appeal, "get_atype_display") else "",
                        str(appeal.start_date) if appeal.start_date else "",
                        str(appeal.end_date) if appeal.end_date else "",
                        str(appeal.num_beneficiaries) if appeal.num_beneficiaries is not None else "",
                        appeal.sector or "",
                        appeal.get_status_display() if hasattr(appeal, "get_status_display") else "",
                    ]
                    appeal_data.append(";".join(parts))
                return " | ".join(appeal_data)
        return ""

    @staticmethod
    def get_molnix_tags_names(obj):
        """Return comma-separated list of molnix tag names"""
        return ", ".join([tag.name for tag in obj.molnix_tags.all()])

    @staticmethod
    def get_molnix_tags_ids(obj):
        """Return comma-separated list of molnix tag IDs"""
        return ", ".join([str(tag.molnix_id) for tag in obj.molnix_tags.all()])

    @staticmethod
    def get_molnix_tags_types(obj):
        """Return comma-separated list of molnix tag types"""
        return ", ".join([tag.tag_type for tag in obj.molnix_tags.all()])


# class UnauthenticatedSurgeAlertSerializer(ModelSerializer):
#     event = MiniEventSerializer()
#     atype_display = serializers.CharField(source='get_atype_display', read_only=True)
#     category_display = serializers.CharField(source='get_category_display', read_only=True)
#
#     class Meta:
#         model = SurgeAlert
#         fields = (
#             'operation', 'deployment_needed', 'is_private', 'event', 'created_at', 'id',
#             'atype', 'atype_display', 'category', 'category_display', 'is_active',
#         )


class SubscriptionSerializer(ModelSerializer):
    country = MiniCountrySerializer()
    event = MiniEventSerializer()
    stype_display = serializers.CharField(source="get_stype_display", read_only=True)
    rtype_display = serializers.CharField(source="get_rtype_display", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "user",
            "country",
            "region",
            "event",
            "dtype",
            "lookup_id",
            "stype",
            "stype_display",
            "rtype",
            "rtype_display",
        )
