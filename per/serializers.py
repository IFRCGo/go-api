import typing
from rest_framework import serializers
from django.utils.translation import gettext
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import Permission

from api.models import Region, Appeal, Country
from api.serializers import RegoCountrySerializer, UserNameSerializer
from .models import (
    Form,
    FormArea,
    FormComponent,
    FormQuestion,
    FormAnswer,
    FormData,
    NSPhase,
    WorkPlan,
    LearningType,
    OpsLearning,
    Overview,
    NiceDocument,
    AssessmentType,
    PerWorkPlan,
    PerWorkPlanComponent,
    FormPrioritization,
    FormPrioritizationComponent,
    PerAssessment,
    AreaResponse,
    FormComponentQuestionAndAnswer,
    FormComponentResponse,
    CustomPerWorkPlanComponent,
    PerFile,
    PerComponentRating,
    PerDocumentUpload,
    FormQuestionGroup
)
from api.serializers import (
    MiniCountrySerializer,
)

# from .admin_classes import RegionRestrictedAdmin
from main.writable_nested_serializers import NestedUpdateMixin, NestedCreateMixin
from drf_spectacular.utils import extend_schema_field
from main.settings import SEP
from utils.file_check import validate_file_type


def check_draft_change(
    instance,
    is_draft: typing.Union[bool, None],
    allow_change_for_non_draft: bool = False,
) -> bool:
    """
    Validate if draft change is allowed
    Respond with draft change status
    """
    if not allow_change_for_non_draft and not instance.is_draft:
        raise serializers.ValidationError("Update is not allowed for non draft")
    # If draft is not provided
    if is_draft is None:
        return False
    # If already is not draft and new status is draft
    if instance.is_draft is False and is_draft is True:
        raise serializers.ValidationError("Can't revert back to draft")
    return instance.is_draft != is_draft


class IsFinalOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Overview
        fields = ("id", "is_finalized")


class FormAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormArea
        fields = ("id", "title", "area_num")


class FormComponentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    # area = FormAreaSerializer()

    class Meta:
        model = FormComponent
        fields = (
            "id",
            "title",
            "component_num",
            "description",
            "area",
            "component_letter",
            "is_parent",
            "has_question_group"
        )


class FormAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormAnswer
        fields = (
            "id",
            "text",
        )


class MiniFormComponentSerializer(serializers.ModelSerializer):
    area = FormAreaSerializer()

    class Meta:
        model = FormComponent
        fields = ("id", "component_num", "title", "area", "description", "component_letter", "is_parent")


class FormQuestionSerializer(serializers.ModelSerializer):
    component = MiniFormComponentSerializer()
    answers = FormAnswerSerializer(many=True)

    class Meta:
        model = FormQuestion
        fields = (
            "component",
            "question",
            "question_num",
            "answers",
            "description",
            "id",
            "question_group"
        )


class MiniFormQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = (
            "component",
            "question",
            "id",
            "question_group"
        )


class MiniQuestionSerailizer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = (
            "id",
            "question",
            "question_num",
        )


class ListFormSerializer(serializers.ModelSerializer):
    area = FormAreaSerializer()
    user = UserNameSerializer()
    overview = IsFinalOverviewSerializer()

    class Meta:
        model = Form
        fields = ("area", "overview", "updated_at", "comment", "user", "id")


class FormStatSerializer(serializers.ModelSerializer):
    area = FormAreaSerializer()
    overview = IsFinalOverviewSerializer()

    class Meta:
        model = Form
        fields = (
            "area",
            "overview",
            "id",
        )


class ListFormDataSerializer(serializers.ModelSerializer):
    selected_answer = FormAnswerSerializer()

    class Meta:
        model = FormData
        fields = ("form", "question_id", "selected_answer", "notes", "id")


class FormDataWOFormSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    selected_answer_details = FormAnswerSerializer(source="selected_answer", read_only=True)
    question_details = MiniQuestionSerailizer(source="question", read_only=True)

    class Meta:
        model = FormData
        fields = ("question", "selected_answer", "notes", "id", "selected_answer_details", "question_details")


class FormAsessmentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    form_data = FormDataWOFormSerializer(many=True)

    class Meta:
        model = Form
        fields = (
            "area",
            "overview",
            "form_data",
            "updated_at",
            "comment",
            "id",
        )

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        form_data = validated_data.pop("form_data")
        form = super().create(validated_data)
        for data in form_data:
            data["form"] = Form.objects.get(id=form.id)
            FormData.objects.create(**data)
        return form


class ListNiceDocSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = NiceDocument
        fields = ("name", "country", "document", "document_url", "visibility", "visibility_display")


class NiceDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = NiceDocument
        fields = "__all__"

    def validate_document(self, document):
        validate_file_type(document)
        return document


class ShortFormSerializer(serializers.ModelSerializer):
    area = FormAreaSerializer()
    overview = IsFinalOverviewSerializer()

    class Meta:
        model = Form
        fields = (
            "area",
            "overview",
            "updated_at",
            "id",
        )


class EngagedNSPercentageSerializer(serializers.ModelSerializer):
    country__count = serializers.IntegerField()
    forms_sent = serializers.IntegerField()

    class Meta:
        model = Region
        fields = (
            "id",
            "country__count",
            "forms_sent",
        )


class GlobalPreparednessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)
    question_id = serializers.CharField(max_length=20)

    class Meta:
        fields = (
            "id",
            "code",
            "question_id",
        )


class NSPhaseSerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)

    class Meta:
        model = NSPhase
        fields = ("id", "country", "phase", "phase_display", "updated_at")


class PerMiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")


class WorkPlanSerializer(serializers.ModelSerializer):
    user = PerMiniUserSerializer()
    prioritization_display = serializers.CharField(source="get_prioritization_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = WorkPlan
        fields = "__all__"


class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = (
            "id",
            "name",
        )


class OverviewSerializer(serializers.ModelSerializer):
    user = PerMiniUserSerializer()
    country = RegoCountrySerializer()
    type_of_assessment = AssessmentTypeSerializer()
    included_forms = serializers.CharField(source="get_included_forms", read_only=True)

    class Meta:
        model = Overview
        fields = "__all__"


class AssessmentRatingSerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    date_of_assessment = serializers.DateField()
    assessment_number = serializers.IntegerField()


class LatestCountryOverviewInputSerializer(serializers.Serializer):
    country_id = serializers.IntegerField(required=True)


class LatestCountryOverviewSerializer(serializers.ModelSerializer):
    type_of_assessment = AssessmentTypeSerializer()
    assessment_ratings = serializers.SerializerMethodField()
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "country_id",
            "assessment_number",
            "date_of_assessment",
            "type_of_assessment",
            "ns_focal_point_name",
            "ns_focal_point_email",
            "assessment_ratings",
            "phase",
            "phase_display",
        )

    @extend_schema_field(AssessmentRatingSerializer(many=True))
    def get_assessment_ratings(self, overview):
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        country_id = overview.country_id
        # also get region from the country
        region_id = overview.country.region_id

        # Check if country admin
        per_admin_country_id = [
            codename.replace('per_country_admin_', '')
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith='per_country_admin_',
            ).values_list('codename', flat=True)
        ]
        per_admin_country_id = list(map(int, per_admin_country_id))
        per_admin_region_id = [
            codename.replace('per_region_admin_', '')
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith='per_region_admin_',
            ).values_list('codename', flat=True)
        ]
        per_admin_region_id = list(map(int, per_admin_region_id))

        if country_id  in per_admin_country_id or region_id in per_admin_region_id or user.is_superuser or user.has_perm("api.per_core_admin"):
            # NOTE: rating_id=1 means Not Reviewed as defined in per/fixtures/componentratings.json
            filters = ~models.Q(
                models.Q(area_responses__component_response__rating__isnull=True) |
                models.Q(area_responses__component_response__rating_id=1),
            )
            qs = (
                PerAssessment.objects.filter(
                    overview__country_id=country_id,
                ).annotate(
                average_rating=models.Avg(
                    "area_responses__component_response__rating__value",
                    filter=filters,
                ),
                    date_of_assessment=models.F("overview__date_of_assessment"),
                    assessment_number=models.F("overview__assessment_number"),
                )
            )
            return AssessmentRatingSerializer(qs, many=True).data
        return None


class PerWorkPlanComponentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    component_details = FormComponentSerializer(source="component", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    supported_by_details = MiniCountrySerializer(source="supported_by", read_only=True)
    supported_by_organization_type_details = serializers.CharField(
        source="get_supported_by_organization_type_display",
        read_only=True
    )

    class Meta:
        model = PerWorkPlanComponent
        fields = (
            "id",
            "component",
            "actions",
            "due_date",
            "status",
            "supported_by",
            "status_display",
            "component_details",
            "supported_by_details",
            "supported_by_organization_type",
            "supported_by_organization_type_details"
        )


class CustomPerWorkPlanComponentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    supported_by_organization_type_details = serializers.CharField(
        source="get_supported_by_organization_type_display",
        read_only=True
    )

    class Meta:
        model = CustomPerWorkPlanComponent
        fields = "__all__"


class MiniOverviewSerializer(serializers.ModelSerializer):
    user_details = PerMiniUserSerializer(source="user", read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "workplan_development_date",
            "user",
            "user_details",
            "ns_focal_point_name",
            "ns_focal_point_email",
        )


class PerWorkPlanSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    prioritized_action_responses = PerWorkPlanComponentSerializer(many=True, required=False)
    additional_action_responses = CustomPerWorkPlanComponentSerializer(many=True, required=False)
    overview_details = MiniOverviewSerializer(source="overview", read_only=True)

    class Meta:
        model = PerWorkPlan
        fields = (
            "id",
            "overview",
            "prioritized_action_responses",
            "additional_action_responses",
            "overview_details",
            "is_draft",
        )

    def create(self, _):
        # NOTE: This is not created manually
        # This is created by FormPrioritizationSerializer
        raise serializers.ValidationError("Create is not allowed")

    def update(self, instance, validated_data):
        overview = validated_data.get("overview")
        is_draft = validated_data.get("is_draft")
        if overview is None:
            raise serializers.ValidationError("Overview is required")
        if is_draft is False:
            overview.update_phase(Overview.Phase.ACTION_AND_ACCOUNTABILITY)
        return super().update(instance, validated_data)


class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = "__all__"


class PerFormDataSerializer(serializers.ModelSerializer):
    form = FormSerializer(required=False)
    question = FormQuestionSerializer(required=False)

    class Meta:
        model = FormData
        fields = "__all__"


class FormComponentQuestionSerializer(serializers.ModelSerializer):
    # formquestion = FormQuestionSerializer(many=True, partial=True)

    class Meta:
        model = FormComponent
        fields = "__all__"


class FormPrioritizationComponentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    component_details = MiniFormComponentSerializer(source="component", read_only=True)

    class Meta:
        model = FormPrioritizationComponent
        fields = ("id", "component", "justification_text", "component_details")


class FormPrioritizationSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    prioritized_action_responses = FormPrioritizationComponentSerializer(many=True, required=False)

    class Meta:
        model = FormPrioritization
        fields = ("id", "overview", "prioritized_action_responses", "is_draft")

    def create(self, _):
        # NOTE: This is not created manually
        # This is created by PerAssessmentSerializer
        raise serializers.ValidationError("Create is not allowed")

    def update(self, instance, validated_data):
        is_draft = validated_data.get("is_draft")
        overview = validated_data.get("overview")
        if overview is None:
            raise serializers.ValidationError("Overview is required")
        if is_draft is False:
            overview.update_phase(Overview.Phase.WORKPLAN)
            PerWorkPlan.objects.get_or_create(overview=overview)
        return super().update(instance, validated_data)


class MiniAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerAssessment
        fields = ("id", "overview")


class PerFileInputSerializer(serializers.Serializer):
    file = serializers.ListField(child=serializers.FileField())


class PerFileSerializer(serializers.ModelSerializer):
    created_by_details = UserNameSerializer(source="created_by", read_only=True)

    class Meta:
        model = PerFile
        fields = "__all__"
        read_only_fields = ("created_by",)

    def validate_file(self, file):
        validate_file_type(file)
        return file

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class PerOverviewSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    type_of_assessment_details = AssessmentTypeSerializer(source="type_of_assessment", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    user_details = UserNameSerializer(source="user", read_only=True)
    assessment_number = serializers.IntegerField(required=False, allow_null=True)
    orientation_documents_details = PerFileSerializer(many=True, read_only=True, source="orientation_documents")

    class Meta:
        model = Overview
        fields = "__all__"

    def create(self, validated_data):
        overview = super().create(validated_data)
        if overview.is_draft:
            overview.update_phase(Overview.Phase.ORIENTATION)
        else:
            overview.update_phase(Overview.Phase.ASSESSMENT)
            # Create associated assessment also
            PerAssessment.objects.create(overview=overview)
        return overview

    def update(self, instance, validated_data):
        # TODO: Add a validation to only allow changes for specific fields after is_draft is False
        is_draft = validated_data.get("is_draft")
        if check_draft_change(instance, is_draft, allow_change_for_non_draft=True) and is_draft is False:
            validated_data["phase"] = Overview.Phase.ASSESSMENT
            # Create associated assessment if not exists already
            PerAssessment.objects.get_or_create(overview=instance)
        return super().update(instance, validated_data)


class PerProcessSerializer(serializers.ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    assessment = serializers.SerializerMethodField()
    prioritization = serializers.SerializerMethodField()
    workplan = serializers.SerializerMethodField()
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)
    type_of_assessment_details = AssessmentTypeSerializer(source="type_of_assessment", read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "assessment_number",
            "date_of_assessment",
            "country",
            "country_details",
            "assessment",
            "prioritization",
            "workplan",
            "created_at",
            "updated_at",
            "phase",
            "phase_display",
            "type_of_assessment",
            "type_of_assessment_details",
            "ns_focal_point_name",
            "ns_focal_point_email",
        )

    def get_assessment(self, obj) -> typing.Optional[int]:
        assessment = PerAssessment.objects.filter(overview=obj).last()
        if assessment:
            return assessment.id
        return None

    def get_prioritization(self, obj) -> typing.Optional[int]:
        prioritization = FormPrioritization.objects.filter(overview=obj).last()
        if prioritization:
            return prioritization.id
        return None

    def get_workplan(self, obj) -> typing.Optional[int]:
        workplan = PerWorkPlan.objects.filter(overview=obj).last()
        if workplan:
            return workplan.id
        return None


class PublicPerProcessSerializer(serializers.ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    assessment = serializers.SerializerMethodField()
    prioritization = serializers.SerializerMethodField()
    workplan = serializers.SerializerMethodField()
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)
    type_of_assessment_details = AssessmentTypeSerializer(source="type_of_assessment", read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "assessment_number",
            "date_of_assessment",
            "country",
            "country_details",
            "assessment",
            "prioritization",
            "workplan",
            "created_at",
            "updated_at",
            "phase",
            "phase_display",
            "type_of_assessment",
            "type_of_assessment_details",
            "ns_focal_point_name",
            "ns_focal_point_email",
        )

    def get_assessment(self, obj) -> typing.Optional[int]:
        assessment = PerAssessment.objects.filter(overview=obj).last()
        if assessment:
            return assessment.id
        return None

    def get_prioritization(self, obj) -> typing.Optional[int]:
        prioritization = FormPrioritization.objects.filter(overview=obj).last()
        if prioritization:
            return prioritization.id
        return None

    def get_workplan(self, obj) -> typing.Optional[int]:
        workplan = PerWorkPlan.objects.filter(overview=obj).last()
        if workplan:
            return workplan.id
        return None


class QuestionResponsesSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    question_details = MiniFormQuestionSerializer(source='question', read_only=True)

    class Meta:
        model = FormComponentQuestionAndAnswer
        fields = (
            "id",
            "question",
            "answer",
            "notes",
            "question_details",
        )


class PerComponentRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerComponentRating
        fields = "__all__"


class FormComponentResponseSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    question_responses = QuestionResponsesSerializer(required=False, many=True)
    rating_details = PerComponentRatingSerializer(source="rating", read_only=True, allow_null=True, required=False)
    component_details = FormComponentSerializer(source="component", read_only=True)

    class Meta:
        model = FormComponentResponse
        fields = (
            "id",
            "component",
            "rating",
            "question_responses",
            "rating_details",
            "component_details",
            "notes",
            # Considerations fields
            "urban_considerations",
            "epi_considerations",
            "climate_environmental_considerations",
        )


class AreaResponseSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    area_details = FormAreaSerializer(source="area", read_only=True)
    component_responses = FormComponentResponseSerializer(
        many=True,
        required=False,
        source="component_response",
    )

    class Meta:
        model = AreaResponse
        fields = (
            "id",
            "area_details",
            "area",
            "component_responses",
        )


class PublicAreaResponseSerializer(serializers.ModelSerializer):
    component_responses = FormComponentResponseSerializer(
        many=True,
        required=False,
        source="component_response",
    )

    class Meta:
        model = AreaResponse
        fields = (
            "id",
            "component_responses",
        )


class PerAssessmentSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    area_responses = AreaResponseSerializer(many=True, required=False)

    class Meta:
        model = PerAssessment
        fields = "__all__"

    def create(self, validated_data):
        # NOTE: This is not created manually
        # This is created by PerOverviewSerializer
        raise serializers.ValidationError("Create is not allowed")

    def update(self, instance, validated_data):
        is_draft = validated_data.get("is_draft")
        if check_draft_change(instance, is_draft) and is_draft is False:
            overview = validated_data.get("overview")
            if overview is None:
                raise serializers.ValidationError("Overview is required")
            overview.update_phase(Overview.Phase.PRIORITIZATION)
            FormPrioritization.objects.create(overview=overview)
        return super().update(instance, validated_data)


class PublicPerCountrySerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)
    type_of_assessment = AssessmentTypeSerializer(read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "date_of_assessment",
            "phase",
            "assessment_number",
            "ns_focal_point_name",
            "ns_focal_point_email",
            "type_of_assessment",
            "phase_display",
        )


# class MiniFormComponentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FormComponent
#         fields = (
#             "id",
#             "status",
#         )


class UserPerCountrySerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)
    type_of_assessment = AssessmentTypeSerializer(read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "date_of_assessment",
            "phase",
            "assessment_number",
            "ns_focal_point_name",
            "ns_focal_point_email",
            "phase_display",
            "type_of_assessment",
        )


class OptionsPerComponentRatingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    value = serializers.IntegerField()


class OptionsFormAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class OptionsAssessmentTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class PerOptionsSerializer(serializers.Serializer):
    componentratings = OptionsPerComponentRatingSerializer(many=True)
    answers = OptionsFormAnswerSerializer(many=True)
    overviewassessmenttypes = OptionsAssessmentTypeSerializer(many=True)


class PublicPerAssessmentSerializer(serializers.ModelSerializer):
    area_responses = PublicAreaResponseSerializer(many=True, required=False)

    class Meta:
        model = PerAssessment
        fields = ("id", "area_responses")


# class OrganizationField(serializers.Field):
#    def to_representation(self, value):
#        if value and instance.is_validated:
#            return value
#        return None


class MiniAppealSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    dtype = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    region_name = serializers.SerializerMethodField()

    @staticmethod
    def get_name(obj):
        return obj.name

    @staticmethod
    def get_start_date(obj):
        return obj.start_date and obj.start_date.year

    @staticmethod
    def get_dtype(obj):
        return obj.dtype and obj.dtype.name

    @staticmethod
    def get_country(obj):
        return obj.country and obj.country.id

    @staticmethod
    def get_region(obj):
        return obj.region and obj.region.id

    @staticmethod
    def get_country_name(obj):
        return obj.country and obj.country.name_en

    @staticmethod
    def get_region_name(obj):
        return obj.region and obj.region.label

    class Meta:
        model = Appeal
        fields = ('code', 'name', 'country', 'region',
            'country_name', 'region_name', 'dtype', 'start_date', 'num_beneficiaries')


class FullAppealSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appeal
        fields = '__all__'


class OpsLearningCSVSerializer(serializers.ModelSerializer):
    # Also the anonyme requests use this, but from
    # get_queryset() only validated records come here in that case.

    type = serializers.SerializerMethodField(read_only=True)
    finding = [''] + [t.label for t in LearningType]
    appeal_code = MiniAppealSerializer(allow_null=True, read_only=True)
    learning = serializers.SerializerMethodField(read_only=True)
    organization = serializers.SerializerMethodField(read_only=True)
    sector = serializers.SerializerMethodField(read_only=True)
    per_component = serializers.SerializerMethodField(read_only=True)
    modified_at = serializers.SerializerMethodField(read_only=True)

    def get_type(self, obj):
        return self.finding[obj.type_validated] if obj.is_validated else self.finding[obj.type]

    @staticmethod
    def get_learning(obj):
        return obj.learning_validated if obj.is_validated else obj.learning

    @staticmethod
    def get_organization(obj):
        if obj.is_validated:
            ret = [x[1] for x in obj.organization_validated.values_list()]
        else:
            ret = [x[1] for x in obj.organization.values_list()]
        return SEP.join(ret)

    @staticmethod
    def get_sector(obj):
        if obj.is_validated:
            ret = [x[1] for x in obj.sector_validated.values_list()]
        else:
            ret = [x[1] for x in obj.sector.values_list()]
        return SEP.join(ret)

    @staticmethod
    def get_per_component(obj):
        if obj.is_validated:
            ret = [x[2] for x in obj.per_component_validated.values_list()]
        else:
            ret = [x[2] for x in obj.per_component.values_list()]
        return SEP.join(ret)

    @staticmethod
    def get_modified_at(obj):
        return obj.modified_at and obj.modified_at.date()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['finding'] = data.pop('type')
        del (data['learning_validated'])
        del (data['type_validated'])
        del (data['organization_validated'])
        del (data['sector_validated'])
        del (data['per_component_validated'])
        del (data['appeal_document_id'])
        del (data['created_at'])
        del (data['is_validated'])
        return data

    class Meta:
        model = OpsLearning
        fields = '__all__'
        read_only_fields = ("modified_at",)


class OpsLearningSerializer(serializers.ModelSerializer):
    appeal_code = FullAppealSerializer(allow_null=True, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['appeal'] = data.pop('appeal_code')
        return data

    class Meta:
        model = OpsLearning
        fields = '__all__'
        read_only_fields = ("created_at", "modified_at")


class OpsLearningInSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpsLearning
        fields = '__all__'


class PublicOpsLearningSerializer(serializers.ModelSerializer):
    # We do not extract appeal details here.
    # Only the validated items are shown, arriving from get_queryset().

    class Meta:
        model = OpsLearning
        read_only_fields = ("created_at", "modified_at")
        exclude = ("learning", "type", "organization", "sector", "per_component")


class PerDocumentUploadSerializer(serializers.ModelSerializer):
    MAX_NUMBER_OF_DOCUMENTS = 10

    class Meta:
        model = PerDocumentUpload
        fields = "__all__"

    def validate(self, data):
        country = data['country']
        per = data.get('per')
        if per:
            user_document_count = PerDocumentUpload.objects.filter(
                country=country,
                created_by=self.context["request"].user,
                per=per
            ).count()
            if user_document_count > self.MAX_NUMBER_OF_DOCUMENTS:
                raise serializers.ValidationError(
                    {
                        "file": gettext("Can add utmost %s documents" % self.MAX_NUMBER_OF_DOCUMENTS)
                    }
                )
        return data

    def validate_per(self, per):
        if per is None:
            raise serializers.ValidationError("This field is required")
        country_per_qs = Country.objects.filter(
            id=self.initial_data['country'],
            per_overviews=per,
        )
        if not country_per_qs.exists():
            raise serializers.ValidationError(
                gettext(
                    "Per %(per)s doesn't match country %(country)s"
                    % {'per': per.id, 'country': self.initial_data['country']}
                )
            )
        return per

    def validate_file(self, file):
        validate_file_type(file)
        return file

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update is not allowed")


class ExportPerViewSerializer(serializers.Serializer):
    status = serializers.CharField()
    url = serializers.CharField(allow_null=True)


class FormQuestionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestionGroup
        fields = "__all__"


class CountryLatestOverviewSerializer(serializers.ModelSerializer):
    phase_display = serializers.CharField(source="get_phase_display", read_only=True)
    type_of_assessment = AssessmentTypeSerializer(read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "date_of_assessment",
            "phase",
            "assessment_number",
            "ns_focal_point_name",
            "ns_focal_point_email",
            "type_of_assessment",
            "phase_display",
        )
