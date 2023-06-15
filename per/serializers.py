from rest_framework import serializers

from django.contrib.auth.models import User

from api.models import Region
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
    Overview,
    NiceDocument,
    AssessmentType,
    PerWorkPlan,
    PerWorkPlanComponent,
    FormPrioritization,
    FormPrioritizationComponent,
    PerAssessment,
    AreaResponse,
    FormComponentConsiderations,
    FormComponentQuestionAndAnswer,
    FormComponentResponse,
    CustomPerWorkPlanComponent,
    PerFile,
    WorkPlanStatus,
)
from api.serializers import (
    MiniCountrySerializer,
)
# from .admin_classes import RegionRestrictedAdmin
from main.writable_nested_serializers import NestedUpdateMixin, NestedCreateMixin


class IsFinalOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Overview
        fields = ("id", "is_finalized")


class FormAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormArea
        fields = (
            'id',
            'title',
            'area_num'
        )


class FormComponentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    # area = FormAreaSerializer()

    class Meta:
        model = FormComponent
        fields = '__all__'


class FormAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormAnswer
        fields = (
            'id',
            'text',
        )


class MiniFormComponentSerializer(serializers.ModelSerializer):
    area = FormAreaSerializer()

    class Meta:
        model = FormComponent
        fields = (
            'id',
            'component_num',
            'title',
            "area"
        )


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
            "is_epi",
            "is_benchmark",
            "description",
            "id",
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


class FormDataWOFormSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    selected_answer_details = FormAnswerSerializer(source='selected_answer', read_only=True)
    question_details = MiniQuestionSerailizer(source='question', read_only=True)

    class Meta:
        model = FormData
        fields = (
            "question",
            "selected_answer",
            "notes",
            "id",
            "selected_answer_details",
            "question_details"
        )


class FormAsessmentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
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
        form_data = validated_data.pop('form_data')
        form = super().create(validated_data)
        for data in form_data:
            data['form'] = Form.objects.get(id=form.id)
            FormData.objects.create(**data)
        return form


class ListNiceDocSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = NiceDocument
        fields = ("name", "country", "document", "document_url", "visibility", "visibility_display")


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


class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")


class WorkPlanSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    prioritization_display = serializers.CharField(source="get_prioritization_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = WorkPlan
        fields = "__all__"


class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = "__all__"


class OverviewSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    country = RegoCountrySerializer()
    type_of_assessment = AssessmentTypeSerializer()
    included_forms = serializers.CharField(source="get_included_forms", read_only=True)

    class Meta:
        model = Overview
        fields = "__all__"


class LatestCountryOverviewSerializer(serializers.ModelSerializer):
    type_of_assessment = AssessmentTypeSerializer()

    class Meta:
        model = Overview
        fields = ("id", "country_id", "assessment_number", "date_of_assessment", "type_of_assessment")


class PerWorkPlanComponentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    component_details = FormComponentSerializer(source="component", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PerWorkPlanComponent
        fields = (
            'id',
            'component',
            'actions',
            'due_date',
            'status',
            'status_display',
            'component_details'
        )


class CustomPerWorkPlanComponentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = CustomPerWorkPlanComponent
        fields = "__all__"


class MiniOverviewSerializer(serializers.ModelSerializer):
    user_details = MiniUserSerializer(source="user", read_only=True)

    class Meta:
        model = Overview
        fields = (
            "id",
            "workplan_development_date",
            "user",
            "user_details",
        )


class PerWorkPlanSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    component_responses = PerWorkPlanComponentSerializer(many=True, required=False)
    custom_component_responses = CustomPerWorkPlanComponentSerializer(many=True, required=False)
    overview_details = MiniOverviewSerializer(source='overview', read_only=True)

    class Meta:
        model = PerWorkPlan
        fields = (
            "id",
            "overview",
            "component_responses",
            "custom_component_responses",
            "overview_details",
        )

    def update(self, instance, validated_data):
        overview = validated_data["overview"]
        if overview:
            Overview.objects.filter(id=overview.id).update(phase=Overview.Phase.WORKPLAN)
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


class FormPrioritizationComponentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    component_details = FormComponentQuestionSerializer(
        source="component",
        read_only=True
    )

    class Meta:
        model = FormPrioritizationComponent
        fields = (
            'id',
            'component',
            'is_prioritized',
            'justification_text',
            'component_details'
        )


class FormPrioritizationSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    component_responses = FormPrioritizationComponentSerializer(many=True, required=False)

    class Meta:
        model = FormPrioritization
        fields = ("id", "overview", "component_responses")

    def create(self, validated_data):
        # overview = validated_data['overview']
        # PerWorkPlan.objects.create(overview=overview)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        overview = validated_data.get('overview')
        Overview.objects.filter(id=overview.id).update(phase=Overview.Phase.PRIORITIZATION)
        if overview:
            PerWorkPlan.objects.create(overview=overview)
        return super().update(instance, validated_data)


class MiniAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerAssessment
        fields = ('id', 'overview')


class PerFileSerializer(serializers.ModelSerializer):
    created_by_details = UserNameSerializer(source="created_by", read_only=True)

    class Meta:
        model = PerFile
        fields = "__all__"
        read_only_fields = ("created_by",)

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class PerOverviewSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    type_of_assessment_details = AssessmentTypeSerializer(source="type_of_assessment", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    user_details = UserNameSerializer(source="user", read_only=True)
    orientation_document_details = PerFileSerializer(source='orientation_document', read_only=True)
    assessment_number = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Overview
        fields = "__all__"

    def create(self, validated_data):
        overview = super().create(validated_data)
        if hasattr(overview, 'date_of_assessment'):
            Overview.objects.filter(id=overview.id).update(phase=Overview.Phase.ORIENTATION)
        # create associated assessment also
        PerAssessment.objects.create(overview=overview)
        return overview

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class PerProcessSerializer(serializers.ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    assessment = serializers.SerializerMethodField()
    prioritization = serializers.SerializerMethodField()
    workplan = serializers.SerializerMethodField()
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)

    class Meta:
        model = Overview
        fields = (
            'id',
            'assessment_number',
            'date_of_assessment',
            'country',
            'country_details',
            'assessment',
            'prioritization',
            'workplan',
            'phase',
            'phase_display',

        )

    def get_assessment(self, obj):
        assessment = PerAssessment.objects.filter(overview=obj).last()
        if assessment:
            return assessment.id
        return None

    def get_prioritization(self, obj):
        prioritization = FormPrioritization.objects.filter(overview=obj).last()
        if prioritization:
            return prioritization.id
        return None

    def get_workplan(self, obj):
        workplan = PerWorkPlan.objects.filter(overview=obj).last()
        if workplan:
            return workplan.id
        return None


class FormComponentConsiderationsSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = FormComponentConsiderations
        fields = (
            'id',
            'urban_considerations',
            'epi_considerations',
            'climate_environmental_conisderations'
        )


class QuestionResponsesSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = FormComponentQuestionAndAnswer
        fields = (
            'id',
            'question',
            'answer',
            'notes',
        )


class FormComponentResponseSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    consideration_responses = FormComponentConsiderationsSerializer(required=False, many=True)
    question_responses = QuestionResponsesSerializer(required=False, many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FormComponentResponse
        fields = (
            'id',
            'component',
            'status',
            'consideration_responses',
            'question_responses',
            'status_display'
        )


class AreaResponseSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    area_details = FormAreaSerializer(
        source='area', read_only=True
    )
    component_responses = FormComponentResponseSerializer(
        many=True,
        required=False,
        source='component_response',
    )

    class Meta:
        model = AreaResponse
        fields = (
            'id',
            'area_details',
            'area',
            'component_responses',
            'is_draft'
        )


class PerAssessmentSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer
):
    area_responses = AreaResponseSerializer(many=True, required=False)

    class Meta:
        model = PerAssessment
        fields = '__all__'

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        overview = validated_data.get('overview')
        is_draft = validated_data.get('is_draft')
        Overview.objects.filter(id=overview.id).update(phase=Overview.Phase.ASSESSMENT)
        if is_draft is False:
            FormPrioritization.objects.create(overview=overview)
        return super().update(instance, validated_data)
