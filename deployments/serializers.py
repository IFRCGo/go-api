from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.utils.translation import gettext
from rest_framework import serializers

from api.serializers import (
    DisasterTypeSerializer,
    ListEventSerializer,
    MiniAdmin2Serializer,
    MiniCountrySerializer,
    MiniDistrictSerializer,
    MiniEventSerializer,
    MiniPersonnelDeploymentSerializer,
    NanoCountrySerializer,
    RelatedAppealSerializer,
    SmallEventForPersonnelCsvSerializer,
    SurgeEventSerializer,
)
from lang.serializers import ModelSerializer
from main.utils import get_merged_items_by_fields
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin

from .models import (
    ERU,
    Admin2,
    AnnualSplit,
    Country,
    District,
    EmergencyProject,
    EmergencyProjectActivity,
    EmergencyProjectActivityAction,
    EmergencyProjectActivityActionSupply,
    EmergencyProjectActivityLocation,
    EmergencyProjectActivitySector,
    ERUOwner,
    ERUReadiness,
    ERUReadinessType,
    Event,
    MolnixTag,
    OperationTypes,
    PartnerSocietyActivities,
    PartnerSocietyDeployment,
    Personnel,
    PersonnelDeployment,
    ProgrammeTypes,
    Project,
    Region,
    RegionalProject,
)


class DeploymentMiniUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class ERUSetSerializer(ModelSerializer):
    deployed_to = MiniCountrySerializer()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ERU
        fields = (
            "type",
            "type_display",
            "units",
            "equipment_units",
            "deployed_to",
            "event",
            "eru_owner",
            "available",
            "id",
        )


class ERUOwnerSerializer(ModelSerializer):
    eru = ERUSetSerializer(many=True, source="eru_set")
    national_society_country = MiniCountrySerializer()

    class Meta:
        model = ERUOwner
        fields = (
            "created_at",
            "updated_at",
            "national_society_country",
            "eru",
            "id",
        )


# ERUSerializer uses ERUOwnerSerializer which uses ERUSetSerializer (~circle)
class ERUSerializer(ModelSerializer):
    deployed_to = MiniCountrySerializer()
    event = ListEventSerializer(allow_null=True, required=False)
    eru_owner = ERUOwnerSerializer()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ERU
        fields = (
            "type",
            "type_display",
            "units",
            "equipment_units",
            "deployed_to",
            "event",
            "eru_owner",
            "available",
            "id",
        )


class ERUOwnerMiniSerializer(ModelSerializer):
    national_society_country_details = MiniCountrySerializer(source="national_society_country", read_only=True)

    class Meta:
        model = ERUOwner
        fields = (
            "id",
            "national_society_country_details",
        )


class ERUMiniSerializer(ModelSerializer):
    eru_owner_details = ERUOwnerMiniSerializer(source="eru_owner", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    deployed_to = MiniCountrySerializer()

    class Meta:
        model = ERU
        fields = (
            "id",
            "type",
            "type_display",
            "units",
            "equipment_units",
            "eru_owner_details",
            "deployed_to",
            "start_date",
            "end_date",
        )


class ListDeployedERUByEventSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    active_erus = ERUMiniSerializer(source="eru_set", many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "appeals",
            "active_erus",
        )


class PersonnelDeploymentSerializer(ModelSerializer):
    country_deployed_to = MiniCountrySerializer(allow_null=True)
    event_deployed_to = SurgeEventSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = (
            "country_deployed_to",
            "region_deployed_to",
            "event_deployed_to",
            "comments",
            "id",
        )


class MolnixTagSerializer(ModelSerializer):
    groups = serializers.SerializerMethodField()

    class Meta:
        fields = ("id", "molnix_id", "name", "description", "color", "tag_type", "groups")
        model = MolnixTag

    @staticmethod
    def get_groups(obj):
        return [t.name for t in obj.groups.all() if not t.is_deprecated]
        # Please don't change ^ to obj.groups.filter(is_deprecated=False) – it creates N+1 queries!!
        # And do not use molnix_tags__groups__is_deprecated check either, due to it can be null.


class PersonnelDeploymentCsvSerializer(ModelSerializer):
    event_deployed_to = SmallEventForPersonnelCsvSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = ("event_deployed_to",)


# 3 versions: a "regular", an Anon(yme) and a Super(user) class:
class PersonnelSerializer(ModelSerializer):
    # For regular logged in users | no molnix_status
    country_from = MiniCountrySerializer(allow_null=True)
    country_to = MiniCountrySerializer(allow_null=True)
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()
    molnix_status = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "molnix_id",
            "molnix_tags",
            "is_active",
            "id",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
            "name",
            "molnix_status",
        )

    def get_name(self, personnel) -> str:
        user = self.context["request"].user
        if user.is_authenticated:
            return personnel.name
        return None

    def get_molnix_status(self, personnel) -> str:
        user = self.context["request"].user
        if user.is_authenticated and user.is_superuser:
            return personnel.molnix_status
        return None


class PersonnelSerializerAnon(ModelSerializer):
    # Not logged in users | no name and molnix_status
    country_from = MiniCountrySerializer(allow_null=True)
    country_to = MiniCountrySerializer(allow_null=True)
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "molnix_id",
            "molnix_tags",
            "is_active",
            "id",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
            "name",
        )


class AggregatedERUAndRapidResponseSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    erus = ERUMiniSerializer(source="eru_set", many=True, read_only=True)
    deployments = MiniPersonnelDeploymentSerializer(source="personneldeployment_set", many=True, read_only=True)
    deployed_eru_count = serializers.IntegerField(read_only=True)
    deployed_personnel_count = serializers.IntegerField(read_only=True)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "erus",
            "deployed_eru_count",
            "deployed_personnel_count",
            "appeals",
            "deployments",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
        )


class PersonnelSerializerSuper(ModelSerializer):
    # Superusers can see molnix_status
    country_from = MiniCountrySerializer(allow_null=True)
    country_to = MiniCountrySerializer(allow_null=True)
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "molnix_id",
            "molnix_tags",
            "is_active",
            "id",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
            "name",
            "molnix_status",  # 2 plus
        )


# Don't forget to adapt drf_views::get_renderer_context if you change this:
class PersonnelCsvSerializerBase(ModelSerializer):
    country_from = NanoCountrySerializer(allow_null=True)
    country_to = NanoCountrySerializer(allow_null=True)
    deployment = PersonnelDeploymentCsvSerializer()
    molnix_sector = serializers.SerializerMethodField()
    molnix_role_profile = serializers.SerializerMethodField()
    molnix_language = serializers.SerializerMethodField()
    molnix_region = serializers.SerializerMethodField()
    molnix_scope = serializers.SerializerMethodField()
    molnix_modality = serializers.SerializerMethodField()
    molnix_operation = serializers.SerializerMethodField()
    ongoing = serializers.SerializerMethodField()
    inactive_status = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    surge_alert_id = serializers.SerializerMethodField()
    appraisal_received = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    @staticmethod
    def get_start_date(obj):
        return obj.start_date.date() if obj.start_date else None

    @staticmethod
    def get_end_date(obj):
        return obj.end_date.date() if obj.end_date else None

    @staticmethod
    def get_molnix_sector(obj):
        return obj.get_tags_for_category("molnix_sector")

    @staticmethod
    def get_molnix_role_profile(obj):
        return obj.get_tags_for_category("molnix_role_profile")

    @staticmethod
    def get_molnix_language(obj):
        return obj.get_tags_for_category("molnix_language")

    @staticmethod
    def get_molnix_region(obj):
        return obj.get_tags_for_category("molnix_region")

    @staticmethod
    def get_molnix_scope(obj):
        return obj.get_tags_for_category("molnix_scope")

    @staticmethod
    def get_molnix_modality(obj):
        return obj.get_tags_for_category("molnix_modality")

    @staticmethod
    def get_molnix_operation(obj):
        return obj.get_tags_for_category("molnix_operation")

    @staticmethod
    def get_inactive_status(obj):
        return obj.molnix_status if obj.molnix_status in ("deleted", "hidden") else None

    @staticmethod
    def get_ongoing(obj):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        start = obj.start_date if obj.start_date else today
        end = obj.end_date if obj.end_date else today
        return start <= today <= end

    @staticmethod
    def get_surge_alert_id(obj):
        return obj.surge_alert_id

    @staticmethod
    def get_appraisal_received(obj):
        return obj.appraisal_received

    @staticmethod
    def get_gender(obj):
        return obj.gender

    @staticmethod
    def get_location(obj):
        return obj.location


# 3 versions: a "regular", an Anon(yme) and a Super(user) class:
class PersonnelCsvSerializer(PersonnelCsvSerializerBase):
    # For logged in users | no molnix_status

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "name",  # plus
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "id",
            "is_active",
            "molnix_sector",
            "molnix_id",
            "molnix_role_profile",
            "molnix_language",
            "molnix_region",
            "molnix_scope",
            "molnix_modality",
            "molnix_operation",
            "ongoing",
            "inactive_status",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
        )


class PersonnelCsvSerializerAnon(PersonnelCsvSerializerBase):
    # Not logged in users | no name and molnix_status

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "id",
            "is_active",
            "molnix_sector",
            "molnix_id",
            "molnix_role_profile",
            "molnix_language",
            "molnix_region",
            "molnix_scope",
            "molnix_modality",
            "molnix_operation",
            "ongoing",
            "inactive_status",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
        )


class PersonnelCsvSerializerSuper(PersonnelCsvSerializerBase):
    # Superusers can see molnix_status

    class Meta:
        model = Personnel
        fields = (
            "start_date",
            "end_date",
            "name",  # plus
            "role",
            "type",
            "country_from",
            "country_to",
            "deployment",
            "id",
            "is_active",
            "molnix_sector",
            "molnix_id",
            "molnix_status",  # plus
            "molnix_role_profile",
            "molnix_language",
            "molnix_region",
            "molnix_scope",
            "molnix_modality",
            "molnix_operation",
            "ongoing",
            "inactive_status",
            "surge_alert_id",
            "appraisal_received",
            "gender",
            "location",
        )


class PartnerDeploymentActivitySerializer(ModelSerializer):

    class Meta:
        model = PartnerSocietyActivities
        fields = (
            "activity",
            "id",
        )


class PartnerDeploymentTableauSerializer(serializers.ModelSerializer):
    parent_society = MiniCountrySerializer()
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = serializers.SerializerMethodField()
    activity = PartnerDeploymentActivitySerializer()

    @staticmethod
    def get_district_deployed_to(obj):
        district_fields = {"name": ""}
        district_deployed_to = obj.district_deployed_to.all()
        if len(district_deployed_to) > 0:
            district_fields["name"] = ", ".join([str(district.name) for district in district_deployed_to])
        return district_fields

    class Meta:
        model = PartnerSocietyDeployment
        fields = (
            "start_date",
            "end_date",
            "name",
            "role",
            "parent_society",
            "country_deployed_to",
            "district_deployed_to",
            "activity",
            "id",
        )


class PartnerDeploymentSerializer(ModelSerializer):
    parent_society = MiniCountrySerializer()
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = MiniDistrictSerializer(many=True)
    activity = PartnerDeploymentActivitySerializer()

    class Meta:
        model = PartnerSocietyDeployment
        fields = (
            "start_date",
            "end_date",
            "name",
            "role",
            "parent_society",
            "country_deployed_to",
            "district_deployed_to",
            "activity",
            "id",
        )


class RegionalProjectSerializer(ModelSerializer):
    class Meta:
        model = RegionalProject
        fields = "__all__"


class AnnualSplitSerializer(ModelSerializer):
    class Meta:
        model = AnnualSplit
        fields = (
            "id",
            "year",
            "budget_amount",  # id: needed for appropriate update
            "target_male",
            "target_female",
            "target_other",
            "target_total",
            "reached_male",
            "reached_female",
            "reached_other",
            "reached_total",
        )


class DeployemntCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "id",
            "name",
            "iso",
            "iso3",
            "society_name",
        )


class DeploymentDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ("id", "name")


class DeploymentRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "name")


class DeploymentAdmin2Serializer(serializers.ModelSerializer):
    district_id = serializers.IntegerField(source="admin1.id", read_only=True)

    class Meta:
        model = Admin2
        fields = (
            "id",
            "name",
            "district_id",
        )


class DeploymentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "id",
            "slug",
            "parent_event",
        )


class ProjectSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    project_country_detail = DeployemntCountrySerializer(source="project_country", read_only=True)
    project_districts_detail = DeploymentDistrictSerializer(source="project_districts", read_only=True, many=True)
    project_admin2_detail = DeploymentAdmin2Serializer(source="project_admin2", read_only=True, many=True)
    reporting_ns_detail = DeployemntCountrySerializer(source="reporting_ns", read_only=True)
    dtype_detail = DisasterTypeSerializer(source="dtype", read_only=True)
    regional_project_detail = RegionalProjectSerializer(source="regional_project", read_only=True)
    event_detail = MiniEventSerializer(source="event", read_only=True)
    primary_sector_display = serializers.CharField(source="primary_sector.title", read_only=True)
    secondary_sectors_display = serializers.SerializerMethodField()
    programme_type_display = serializers.CharField(source="get_programme_type_display", read_only=True)
    operation_type_display = serializers.CharField(source="get_operation_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    annual_splits = AnnualSplitSerializer(many=True, required=False)
    modified_by_detail = DeploymentMiniUserSerializer(source="modified_by", read_only=True)

    @staticmethod
    def get_secondary_sectors_display(obj) -> list:
        return [t.title for t in obj.secondary_sectors.all()]

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("user", "modified_by")
        extra_kwargs = {
            field: {
                "allow_null": False,
                "required": True,
            }
            for field in (
                "reporting_ns",
                "name",
                "project_country",
                "programme_type",
                "primary_sector",
                "project_districts",
            )
        }

    def validate(self, data):
        d_project_districts = data["project_districts"]
        # Override country with district's country
        if isinstance(d_project_districts, list) and len(d_project_districts):
            data["project_country"] = data["project_districts"][0].country
            for project in data["project_districts"][1:]:
                if project.country != data["project_country"]:
                    raise serializers.ValidationError(gettext("Different country found for given districts"))
        if (
            data["operation_type"] == OperationTypes.EMERGENCY_OPERATION
            and data["programme_type"] == ProgrammeTypes.MULTILATERAL
            and data.get("event") is None
        ):
            raise serializers.ValidationError(
                gettext("Event should be provided if operation type is Emergency Operation and programme type is Multilateral")
            )
        return data

    def create(self, validated_data):
        project = super().create(validated_data)
        # create does not bear the non-Project extra fields (which are needed for AnnualSplits), so we must đouble:
        if self.context and "request" in self.context:
            if "is_annual_report" in self.context["request"].data:
                project.is_annual_report = self.context["request"].data["is_annual_report"]
            # if 'annual_split_detail' in self.context['request'].data:
            #     project.annual_split_detail = self.context['request'].data['annual_split_detail']
        project.user = self.context["request"].user
        project.save()
        return project

    def update(self, instance, validated_data):
        validated_data["modified_by"] = self.context["request"].user
        if self.context and "request" in self.context:  # code đuplication
            if "is_annual_report" in self.context["request"].data:
                validated_data["is_annual_report"] = self.context["request"].data["is_annual_report"]
            # if 'annual_split_detail' in self.context['request'].data:
            #     validated_data['annual_split_detail'] = self.context['request'].data['annual_split_detail']
        return super().update(instance, validated_data)


class ProjectCsvSerializer(ProjectSerializer):
    secondary_sectors = serializers.SerializerMethodField()
    secondary_sectors_display = serializers.SerializerMethodField()
    project_districts_detail = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ["project_districts"]

    @staticmethod
    def get_secondary_sectors(obj):
        return ", ".join([str(t.id) for t in obj.secondary_sectors.all()])

    @staticmethod
    def get_secondary_sectors_display(obj):
        return ", ".join([t.title for t in obj.secondary_sectors.all()])

    @staticmethod
    def get_project_districts_detail(obj):
        return get_merged_items_by_fields(obj.project_districts.all(), ["name", "code", "id", "is_enclave", "is_deprecated"])


class CharKeyValueSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()

    @staticmethod
    def choices_to_data(choices):
        return [
            {
                "key": key,
                "value": value,
            }
            for key, value in choices
        ]


# ------ Emergency Project -- [Start]
class EmergencyProjectActivitySectorSerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivitySector
        fields = (
            "id",
            "title",
            "order",
        )


class EmergencyProjectActivityActionSupplySerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivityActionSupply
        fields = (
            "id",
            "title",
            "order",
        )


class EmergencyProjectActivityActionSerializer(ModelSerializer):
    supplies_details = EmergencyProjectActivityActionSupplySerializer(
        source="supplies",
        read_only=True,
        many=True,
    )

    class Meta:
        model = EmergencyProjectActivityAction
        fields = ("id", "sector", "title", "order", "supplies_details", "description", "is_cash_type", "has_location")


class EmergencyProjectActivityLocationSerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivityLocation
        fields = "__all__"


class EmergencyProjectOptionsSerializer(serializers.Serializer):
    sectors = EmergencyProjectActivitySectorSerializer(read_only=True, many=True)
    actions = EmergencyProjectActivityActionSerializer(read_only=True, many=True)


class EmergencyProjectActivitySerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    supplies = serializers.DictField(child=serializers.IntegerField(), required=False)
    custom_supplies = serializers.DictField(
        child=serializers.IntegerField(),
    )
    points = EmergencyProjectActivityLocationSerializer(many=True, required=False)
    sector_details = EmergencyProjectActivitySectorSerializer(source="sector", read_only=True)
    action_details = EmergencyProjectActivityActionSerializer(source="action", read_only=True)

    class Meta:
        model = EmergencyProjectActivity
        exclude = ("project",)

    def validate(self, data):
        sector = data.get("sector", self.instance and self.instance.sector)
        action = data.get("action", self.instance and self.instance.action)
        supplies = data.get("supplies")
        if action:
            data["sector"] = sector = action.sector
        if sector is None:
            raise serializers.ValidationError({"sector": gettext("This is required, Or provide a valid action.")})
        if supplies:
            supplies_keys = supplies.keys()
            action_supplies_id = list(action.supplies.values_list("id", flat=True))
            if invalid_keys := [key for key in supplies_keys if int(key) not in action_supplies_id]:
                raise serializers.ValidationError(
                    {
                        "supplies": gettext("Invalid supplies keys: %s" % ", ".join(invalid_keys)),
                    }
                )
        return data


class EmergencyProjectSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer,
):
    created_by_details = DeploymentMiniUserSerializer(source="created_by", read_only=True)
    modified_by_details = DeploymentMiniUserSerializer(source="modified_by", read_only=True)
    event_details = MiniEventSerializer(source="event", read_only=True)
    reporting_ns_details = MiniCountrySerializer(source="reporting_ns", read_only=True, allow_null=True, required=False)
    deployed_eru_details = ERUMiniSerializer(source="deployed_eru", read_only=True)
    districts_details = MiniDistrictSerializer(source="districts", read_only=True, many=True)
    admin2_details = MiniAdmin2Serializer(source="admin2", read_only=True, many=True)
    activities = EmergencyProjectActivitySerializer(many=True, required=False)
    # Enums
    activity_lead_display = serializers.CharField(source="get_activity_lead_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = EmergencyProject
        fields = (
            "id",
            "created_by_details",
            "modified_by_details",
            "reporting_ns_details",
            "deployed_eru_details",
            "districts_details",
            "activities",
            "event_details",
            "activity_lead_display",
            "status_display",
            "country_details",
            "visibility_display",
            "title",
            "activity_lead",
            "reporting_ns",
            "event",
            "country",
            "districts",
            "status",
            "created_at",
            "modified_at",
            "start_date",
            "end_date",
            "admin2",
            "admin2_details",
            "reporting_ns_contact_name",
            "reporting_ns_contact_role",
            "reporting_ns_contact_email",
            "deployed_eru",
        )  # '__all__' | Both X_details + X fields are needed: outgoing + incoming data.
        read_only_fields = (
            "created_by",
            "created_at",
            "modified_by",
            "modified_at",
        )

    def validate(self, data):
        reporting_ns = data.get("reporting_ns", self.instance and self.instance.reporting_ns)
        deployed_eru = data.get("deployed_eru", self.instance and self.instance.deployed_eru)
        country = data.get("country", None)
        for district in data.get("districts") or []:
            if district.country_id != country.id:
                raise serializers.ValidationError(
                    {
                        "districts": gettext("All region/province should be from selected country"),
                    }
                )
        if data["activity_lead"] == EmergencyProject.ActivityLead.NATIONAL_SOCIETY:
            if reporting_ns is None:
                raise serializers.ValidationError(
                    {
                        "reporting_ns": gettext("Reporting NS is required when National Society is leading the activity"),
                    }
                )
        else:
            if deployed_eru is None:
                raise serializers.ValidationError(
                    {
                        "deployed_eru": gettext("Deployed ERU is required when Deployed ERU is leading the activity"),
                    }
                )
        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# ------ Emergency Project -- [End]


class AggregateDeploymentsSerializer(serializers.Serializer):
    rapid_response_deployments_this_year = serializers.IntegerField(required=True)
    active_emergency_response_units = serializers.IntegerField(required=True)
    emergency_response_unit_deployed_this_year = serializers.IntegerField(required=True)
    active_rapid_response_personnel = serializers.IntegerField(required=True)


class ProjectPerSector(serializers.Serializer):
    primary_sector = serializers.IntegerField()
    primary_sector_display = serializers.CharField()
    count = serializers.IntegerField()


class GlobalProjectNSOngoingProjectsStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    iso3 = serializers.CharField()
    society_name = serializers.CharField()
    ongoing_projects = serializers.IntegerField(allow_null=True, required=False)
    target_total = serializers.IntegerField(allow_null=True, required=False)
    budget_amount_total = serializers.IntegerField(allow_null=True, required=False)
    operation_types = serializers.ListField(child=serializers.IntegerField(), required=False, allow_null=True)
    projects_per_sector = ProjectPerSector(many=True, required=False)
    operation_types_display = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)


class OverviewProjectsPerSector(serializers.Serializer):
    primary_sector = serializers.IntegerField()
    primary_sector_display = serializers.CharField()
    count = serializers.IntegerField()


class OverviewProjectsPerProgrammeType(serializers.Serializer):
    programme_type = serializers.IntegerField()
    programme_type_display = serializers.CharField()
    count = serializers.IntegerField()


class OverviewProjectsPerSecondarySectors(serializers.Serializer):
    secondary_sectors = serializers.IntegerField()
    secondary_sectors_display = serializers.CharField()
    count = serializers.IntegerField()


class GlobalProjectOverviewSerializer(serializers.Serializer):
    total_ongoing_projects = serializers.IntegerField(allow_null=True, required=False)
    ns_with_ongoing_activities = serializers.IntegerField(allow_null=True, required=False)
    target_total = serializers.IntegerField(allow_null=True, required=False)
    projects_per_sector = OverviewProjectsPerSector(many=True, allow_null=True)
    projects_per_programme_type = OverviewProjectsPerProgrammeType(many=True, allow_null=True)
    projects_per_secondary_sectors = OverviewProjectsPerSecondarySectors(many=True, allow_null=True)


class DeploymentByNSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    society_name = serializers.CharField()
    deployments_count = serializers.IntegerField(allow_null=True, required=False)


class DeploymentsByMonthSerializer(serializers.Serializer):
    date = serializers.CharField()
    count = serializers.IntegerField()


class ProjectRegionOverviewStatusSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    count = serializers.IntegerField()


class ProjectRegionOverviewSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField(allow_null=True)
    ns_with_ongoing_activities = serializers.IntegerField(allow_null=True)
    total_budget = serializers.IntegerField(allow_null=True)
    target_total = serializers.IntegerField(allow_null=True)
    reached_total = serializers.IntegerField(allow_null=True)
    projects_by_status = ProjectRegionOverviewStatusSerializer(allow_null=True, many=True)


class ProjectRegionMovementActivitiesCountrySerializer(serializers.Serializer):
    iso3 = serializers.CharField()
    iso = serializers.CharField()
    id = serializers.IntegerField()
    projects_count = serializers.IntegerField()
    planned_projects_count = serializers.IntegerField()
    ongoing_projects_count = serializers.IntegerField()
    completed_projects_count = serializers.IntegerField()
    name = serializers.CharField()


class ProjectRegionMovementActivitiesReportingNSSector(serializers.Serializer):
    id = serializers.IntegerField()
    sector = serializers.CharField()
    count = serializers.IntegerField(allow_null=True)


class ProjectRegionMovementActivitiesReportingNS(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    sectors = ProjectRegionMovementActivitiesReportingNSSector(many=True)


class ProjectRegionMovementActivitiesCountrySectorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    reporting_national_societies = ProjectRegionMovementActivitiesReportingNS(many=True)


class ProjectRegionMovementActivitiesSupportingNSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class ProjectRegionMovementActivitiesSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField(allow_null=True)
    countries_count = ProjectRegionMovementActivitiesCountrySerializer(many=True)
    country_ns_sector_count = ProjectRegionMovementActivitiesCountrySectorSerializer(many=True)
    supporting_ns = ProjectRegionMovementActivitiesSupportingNSSerializer(many=True)


class ERUReadinessTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    equipment_readiness_display = serializers.CharField(source="get_equipment_readiness_display", read_only=True)
    people_readiness_display = serializers.CharField(source="get_people_readiness_display", read_only=True)
    funding_readiness_display = serializers.CharField(source="get_funding_readiness_display", read_only=True)

    class Meta:
        model = ERUReadinessType
        fields = "__all__"


class ERUReadinessSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer,
):
    eru_owner = serializers.PrimaryKeyRelatedField(
        queryset=ERUOwner.objects.prefetch_related("national_society_country"),
        required=True,
        write_only=True,
    )
    eru_owner_details = ERUOwnerMiniSerializer(source="eru_owner", read_only=True)
    eru_types = ERUReadinessTypeSerializer(
        many=True,
        required=True,
    )

    class Meta:
        model = ERUReadiness
        fields = "__all__"

    def validate_eru_types(self, value):
        eru_types = [eru_type["type"] for eru_type in value]

        if len(eru_types) != len(set(eru_types)):
            raise serializers.ValidationError({"eru_types": gettext("eru type should be unique")})
        return value

    def validate(self, attrs):
        eru_readiness_types = attrs.get("eru_types", [])
        # Check if ERU Readiness type is already used in another ERUReadiness
        if self.instance and eru_readiness_types:
            eru_types_id = [eru_type["id"] for eru_type in eru_readiness_types if "id" in eru_type]
            if (
                len(eru_types_id) != len(set(eru_types_id))
                or ERUReadiness.objects.filter(eru_types__in=eru_types_id).exclude(id=self.instance.id).exists()
            ):
                raise serializers.ValidationError({"eru_types": gettext("one or more eru readiness type is already used.")})

        return attrs


class MiniERUReadinessSerializer(serializers.ModelSerializer):
    eru_owner_details = ERUOwnerMiniSerializer(source="eru_owner", read_only=True)

    class Meta:
        model = ERUReadiness
        fields = (
            "id",
            "eru_owner_details",
            "updated_at",
        )


# Creating different serializer to avoid circular serializer(eru_types:M2M)
class MiniERUReadinessTypeSerializer(serializers.ModelSerializer):
    eru_readiness = MiniERUReadinessSerializer(source="erureadiness_set", read_only=True, many=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    equipment_readiness_display = serializers.CharField(source="get_equipment_readiness_display", read_only=True)
    people_readiness_display = serializers.CharField(source="get_people_readiness_display", read_only=True)
    funding_readiness_display = serializers.CharField(source="get_funding_readiness_display", read_only=True)

    class Meta:
        model = ERUReadinessType
        fields = "__all__"
