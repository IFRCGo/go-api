import docx
from rest_framework import serializers

from typing import Any, List

from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedInterventionIndicators,
    RiskSecurity
)
from api.models import (
    DisasterType,
    Country,
)

from .common_utils import (
    parse_int,
    parse_date,
    parse_float,
    get_text_or_null,
    parse_string_to_int,
    parse_boolean,
    get_table_data,
    parse_disaster_category,
)


def parse_national_society_title(title):
    title_dict = {
        'National Society Readiness': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
        'Assessments': NationalSocietyAction.Title.ASSESSMENT,
        'Coordination': NationalSocietyAction.Title.COORDINATION,
        'Resource Mobilization': NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
        'Activation of contingency plans': NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
        'EOC': NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
        'Shelter, Housing and Settlements': NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Livelihoods and Basic Needs': NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health': NationalSocietyAction.Title.HEALTH,
        'Water Sanitation and Hygiene': NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
        'Protection, Gender and Inclusion': NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': NationalSocietyAction.Title.EDUCATION,
        'Migration': NationalSocietyAction.Title.MIGRATION,
        'Risk Reduction, Climate Adaptation and Recovery': NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Community Engagement and Accountability': NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
        'Environment Sustainability': NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
        'Other': NationalSocietyAction.Title.OTHER,

    }
    return title_dict.get(title)


def parse_identified_need_title(title):
    title_dict = {
        'Livelihoods': IdentifiedNeed.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health & Care': IdentifiedNeed.Title.HEALTH,
        'Water, Sanitation and Hygiene (WASH)': IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE,
        'Risk Reduction, Climate adaptation and Recovery': IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Shelter, Housing and Settlements': IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Multi-purpose Cash': IdentifiedNeed.Title.MULTI_PURPOSE_CASH_GRANTS,
        'Protection, Gender, and Inclusion (PGI)': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': IdentifiedNeed.Title.EDUCATION,
        'Migration': IdentifiedNeed.Title.MIGRATION,
        'Environmental Sustainability': IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
    }
    return title_dict.get(title)


def parse_planned_intervention_title(title):
    title_dict = {
        'Shelter, Housing and Settlements': PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Livelihoods And Basic Needs': PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health': PlannedIntervention.Title.HEALTH,
        'Water, Sanitation And Hygiene': PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE,
        'Protection, Gender And Inclusion': PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': PlannedIntervention.Title.EDUCATION,
        'Migration': PlannedIntervention.Title.MIGRATION,
        'Risk Reduction, Climate Adaptation And Recovery': PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Environmental Sustainability': PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY,
        'Secretariat Services': PlannedIntervention.Title.SECRETARIAT_SERVICES,
        'National Society Strengthening': PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING,
        'Multi-purpose Cash': PlannedIntervention.Title.MULTI_PURPOSE_CASH,
        'Community Engagement and Accountability': PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,


    }
    return title_dict.get(title)


def parse_disaster_type(disaster_type):
    return DisasterType.objects.filter(name__icontains=disaster_type).first()


def parse_type_of_onset(onset_type):
    if onset_type == 'Slow':
        return Dref.OnsetType.SLOW
    elif onset_type == 'Sudden':
        return Dref.OnsetType.SUDDEN
    elif onset_type == 'Imminent':
        return Dref.OnsetType.IMMINENT
    return None


def extract_imminent_file(doc, created_by):
    tables = get_table_data(doc)

    # Get item form an array
    def _t(items: List[Any], index=0):
        if items and len(items) > index:
            return items[index]
        return None

    def get_table_cells(table_idx):
        table = tables[table_idx]
        def f(r, c, i=0, as_list=False):
            if as_list:
                return table[r][c]
            return _t(table[r][c], i)
        return f
    document = docx.Document(doc)
    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    paragraph2 = document.paragraphs[1]
    paragraph_element2 = paragraph2._element.xpath('.//w:t')
    data['title'] = get_text_or_null(paragraph_element2)
    if not data['title']:
        raise serializers.ValidationError('A title is required')

    cells = get_table_cells(0)
    data['appeal_code'] = cells(1, 0)
    data['amount_requested'] = parse_string_to_int(cells(1, 1, 1))
    data['disaster_category'] = parse_disaster_category(cells(1, 2))
    data['disaster_type'] = parse_disaster_type(cells(1, 4))
    data['glide_code'] = cells(3, 0)
    data['num_affected'] = parse_string_to_int(cells(3, 1))
    data['num_assisted'] = parse_string_to_int(cells(3, 2))
    data['type_of_onset'] = parse_type_of_onset(cells(5, 0))
    data['date_of_approval'] = parse_date(cells(5, 1))
    data['end_date'] = parse_date(cells(5, 2))
    data['operation_timeframe'] = parse_int(cells(5, 3))
    country = Country.objects.filter(name__icontains=cells(6, 0, 1)).first()
    if country is None:
        raise serializers.ValidationError('A valid country name is required')
    data['country'] = country

    paragraph6 = document.paragraphs[7]._element.xpath('.//w:t')
    event_desc = []
    if len(paragraph6) > 0:
        for desc in paragraph6:
            event_desc.append(desc.text)
    data['event_text'] = ''.join(event_desc) if event_desc else None

    paragraph8 = document.paragraphs[9]._element.xpath('.//w:t')
    event_description = []
    if len(paragraph8) > 0:
        for desc in paragraph8:
            event_description.append(desc.text)
    data['event_description'] = ''.join(event_description) if event_description else None
    paragraph11 = document.paragraphs[11]._element.xpath('.//w:t')
    anticipatory_actions_desc = []
    if len(paragraph11) > 0:
        for desc in paragraph11:
            anticipatory_actions_desc.append(desc.text)
    data['anticipatory_actions'] = ''.join(anticipatory_actions_desc) if anticipatory_actions_desc else None
    paragraph13 = document.paragraphs[13]._element.xpath('.//w:t')
    event_scope_description = []
    if len(paragraph13) > 0:
        for desc in paragraph13:
            event_scope_description.append(desc.text)
    data['event_scope'] = ''.join(event_scope_description) if event_scope_description else None

    # Previous Operation
    # NOTE: I am not sure about the index 1 being used below - Bibek
    table1 = document.tables[1]
    cells = get_table_cells(1)

    data['affect_same_area'] = parse_boolean(cells(0, 1))
    data['affect_same_population'] = parse_boolean(cells(1, 1))
    data['ns_respond'] = parse_boolean(cells(2, 1))
    data['ns_request_fund'] = parse_boolean(cells(3, 1))
    data['ns_request_text'] = cells(4, 1)
    if cells(4, 1) == 'Yes':
        table_one_row_five_column_one = table1.cell(5, 1)._tc.xpath('.//w:t')
        data['dref_recurrent_text'] = get_text_or_null(table_one_row_five_column_one)
    if cells(0, 1) == 'Yes' and \
            cells(1, 1) == 'Yes' and \
            cells(2, 1) == 'Yes' and \
            cells(3, 1) == 'Yes' and \
            cells(4, 1) == 'Yes':
        table_one_row_seven_column_one = table1.cell(7, 1)._tc.xpath('.//w:t')
        recurrent_text = []
        if len(table_one_row_seven_column_one) > 0:
            for desc in table_one_row_seven_column_one:
                recurrent_text.append(desc.text)
        data['dref_recurrent_text'] = ''.join(recurrent_text) if recurrent_text else None

    # TODO: uncomment this. However it was not being used. This was creating error
    # so has been commented out
    # table_one_row_eight_column_zero = table1.cell(8, 0)._tc.xpath('.//w:t')
    lessons_learned_text = []
    if len(lessons_learned_text) > 0:
        for desc in lessons_learned_text:
            lessons_learned_text.append(desc.text)
    data['lessons_learned'] = ''.join(lessons_learned_text) if lessons_learned_text else None
    # National Socierty Actions
    cells = get_table_cells(1)
    # National Society
    national_society_actions = []
    national_society_titles = [
        NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
        NationalSocietyAction.Title.ASSESSMENT,
        NationalSocietyAction.Title.COORDINATION,
        NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
        NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
        NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
        NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        NationalSocietyAction.Title.HEALTH,
        NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
        NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
        NationalSocietyAction.Title.EDUCATION,
        NationalSocietyAction.Title.MIGRATION,
        NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
        NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
        NationalSocietyAction.Title.MULTI_PURPOSE_CASH,
        NationalSocietyAction.Title.OTHER,
    ]
    for i, title in enumerate(national_society_titles):
        description = cells(i, 1)
        if description:
             national_society_actions.append({
                'title': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
                'description': description
            })

    # Create national Society objects db level
    national_societys = []
    for national_data in national_society_actions:
        national = NationalSocietyAction.objects.create(**national_data)
        national_societys.append(national)

    cells = get_table_cells(2)
    ifrc_desc = cells(0, 1, as_list=True) or []

    data['ifrc'] = ''.join(ifrc_desc) if ifrc_desc else None
    partner_national_society_desc = cells(1, 1, as_list=True) or []
    data['partner_national_society'] = ''.join(partner_national_society_desc) if partner_national_society_desc else None

    icrc_desc = cells(2, 1, as_list=True) or []
    data['icrc'] = ''.join(icrc_desc) if icrc_desc else None

    # Other actors
    cells = get_table_cells(3)
    data['government_requested_assistance'] = parse_boolean(cells(0, 1))
    national_authorities = cells(1, 1, as_list=True) or []
    data['national_authorities'] = ''.join(national_authorities) if national_authorities else None

    un_and_other_actors = cells(2, 0, as_list=True) or []
    data['un_or_other_actor'] = ''.join(un_and_other_actors) if un_and_other_actors else None

    coordination_mechanism = cells(3, 1, as_list=True) or []
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism) if coordination_mechanism else None

    operation_objective = document.paragraphs[29]._element.xpath('.//w:t')
    operation_description = []
    if len(operation_objective) > 0:
        for desc in operation_objective:
            operation_description.append(desc.text)
    data['operation_objective'] = ''.join(operation_description) if operation_description else None
    # targeting strategy
    response_strategy = document.paragraphs[31]._element.xpath('.//w:t')
    response_description = []
    if len(response_strategy) > 0:
        for desc in response_strategy:
            response_description.append(desc.text)
    data['response_strategy'] = ''.join(response_description) if response_description else None

    paragraph40 = document.paragraphs[33]._element.xpath('.//w:t')
    people_assisted_description = []
    if len(paragraph40) > 0:
        for desc in paragraph40:
            people_assisted_description.append(desc.text)
    data['people_assisted'] = ''.join(people_assisted_description) if people_assisted_description else None
    paragraph42 = document.paragraphs[35]._element.xpath('.//w:t')
    selection_criteria_description = []
    if len(paragraph42) > 0:
        for desc in paragraph42:
            selection_criteria_description.append(desc.text)
    data['selection_criteria'] = ''.join(selection_criteria_description) if selection_criteria_description else None

    # Targeting Population
    cells = get_table_cells(4)
    data['women'] = parse_string_to_int(cells(0, 1))
    data['girls'] = parse_string_to_int(cells(1, 1))
    data['men'] = parse_string_to_int(cells(2, 1))
    data['boys'] = parse_string_to_int(cells(3, 1))
    data['total_targeted_population'] = parse_string_to_int(cells(4, 1))
    data['people_per_local'] = parse_float(cells(1, 2))
    data['people_per_urban'] = parse_float(cells(1, 3))
    data['disability_people_per'] = parse_float(cells(3, 2))
    # TODO: the following data was not in imminent docs so null set
    # data['people_targeted_with_early_actions'] = parse_int(cells(4, 4))
    data['people_targeted_with_early_actions'] = None

    # Risk And Security Considerations
    cells = get_table_cells(5)
    mitigation_actions = []
    for i in range(2, 5):
        risk = cells(i, 0)
        mitigation = cells(i, 1)
        data_row = {
            'risk': risk,
            'mitigation': mitigation,
        }
        mitigation_actions.append(data_row)

    mitigation_list = []
    for action in mitigation_actions:
        risk_security = RiskSecurity.objects.create(**action)
        mitigation_list.append(risk_security)
    data['risk_security_concern'] = cells(6, 0)

    # PlannedIntervention Table
    planned_intervention = []
    for i in range(6, 19):
        cells = get_table_cells(i)
        title = cells(0, 1, 0)
        budget = cells(0, 3, 1)
        targated_population = cells(1, 3)

        indicators = []
        for j in range(3, 6):
            indicators.append({
                'title': cells(j, 0),
                'target': parse_int(cells(j, 2)),
            })
        indicators_object_list = []
        for indicator in indicators:
            if indicator['title'] is None:
                continue
            planned_object = PlannedInterventionIndicators.objects.create(**indicator)
            indicators_object_list.append(planned_object)

        priority_description = cells(6, 1)
        planned_data = {
            'title': parse_planned_intervention_title(title),
            'budget': parse_int(budget),
            'person_targeted': parse_int(targated_population),
            'description': priority_description
        }

        planned = PlannedIntervention.objects.create(**planned_data)
        planned.indicators.add(*indicators_object_list)
        planned_intervention.append(planned)

    # About Support Service
    paragraph53 = document.paragraphs[53]._element.xpath('.//w:t')
    human_resource_description = []

    if len(paragraph53) > 0:
        for desc in paragraph53:
            human_resource_description.append(desc.text)

    data['human_resource'] = ''.join(human_resource_description) if human_resource_description else None

    paragraph55 = document.paragraphs[55]._element.xpath('.//w:t')
    surge_personnel_deployed_description = []
    if len(paragraph55) > 0:
        for desc in paragraph55:
            surge_personnel_deployed_description.append(desc.text)
    data['surge_personnel_deployed'] = ''.join(surge_personnel_deployed_description) if surge_personnel_deployed_description else None

    # TODO: set none because did not find corresponding data in docx
    # paragraph70 = document.paragraphs[66]._element.xpath('.//w:t')
    # logistic_capacity_of_ns_description = []
    # if len(paragraph70) > 0:
    #     for desc in paragraph70:
    #         logistic_capacity_of_ns_description.append(desc.text)
    # data['logistic_capacity_of_ns'] = ''.join(logistic_capacity_of_ns_description) if logistic_capacity_of_ns_description else None
    data['logistic_capacity_of_ns'] = None

    # paragraph73 = document.paragraphs[69]._element.xpath('.//w:t')
    # pmer_description = []
    # if len(paragraph73) > 0:
    #     for desc in paragraph73:
    #         pmer_description.append(desc.text)
    # data['pmer'] = ''.join(pmer_description) if pmer_description else None
    data['pmer'] = None

    # paragraph75 = document.paragraphs[71]._element.xpath('.//w:t')
    # communication_description = []
    # if len(paragraph75) > 0:
    #     for desc in paragraph75:
    #         communication_description.append(desc.text)
    # data['communication'] = ''.join(communication_description) if communication_description else None
    data['communication'] = None

    # Contact Information
    paragraph63 = document.paragraphs[63]._element.xpath('.//w:t')
    national_society_contact = []
    for paragraph in paragraph63:
        national_society_contact.append(paragraph.text)

    data['national_society_contact_title'] = national_society_contact[3]
    data['national_society_contact_email'] = national_society_contact[5]
    data['national_society_contact_phone_number'] = national_society_contact[7]
    data['national_society_contact_name'] = national_society_contact[0]

    paragraph64 = document.paragraphs[64]._element.xpath('.//w:t')
    ifrc_appeal_manager = []
    for paragraph in paragraph64:
        ifrc_appeal_manager.append(paragraph.text)

    data['ifrc_appeal_manager_title'] = ifrc_appeal_manager[3]
    data['ifrc_appeal_manager_email'] = ifrc_appeal_manager[5]
    data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager[7]
    data['ifrc_appeal_manager_name'] = ifrc_appeal_manager[0]

    paragraph65 = document.paragraphs[65]._element.xpath('.//w:t')
    ifrc_project_manager = []
    for paragraph in paragraph65:
        ifrc_project_manager.append(paragraph.text)
    data['ifrc_project_manager_title'] = ifrc_project_manager[3]
    data['ifrc_project_manager_email'] = ifrc_project_manager[5]
    data['ifrc_project_manager_phone_number'] = ifrc_project_manager[7]
    data['ifrc_project_manager_name'] = ifrc_project_manager[0]

    paragraph66 = document.paragraphs[66]._element.xpath('.//w:t')
    ifrc_emergency = []
    for paragraph in paragraph66:
        ifrc_emergency.append(paragraph.text)
    data['ifrc_emergency_title'] = ifrc_emergency[3]
    data['ifrc_emergency_email'] = ifrc_emergency[5]
    data['ifrc_emergency_phone_number'] = ifrc_emergency[7]
    data['ifrc_emergency_name'] = ifrc_emergency[0]

    paragraph67 = document.paragraphs[67]._element.xpath('.//w:t')
    media = []
    for paragraph in paragraph67:
        media.append(paragraph.text)
    data['media_contact_title'] = media[3]
    data['media_contact_email'] = media[5]
    data['media_contact_phone_number'] = media[7]
    data['media_contact_name'] = media[0]

    data['is_published'] = False
    data['national_society'] = country
    data['created_by'] = created_by

    dref = Dref.objects.create(**data)
    dref.planned_interventions.add(*planned_intervention)
    # NOTE: No need needs for imminent
    # dref.needs_identified.add(*needs)
    dref.national_society_actions.add(*national_societys)
    dref.risk_security.add(*mitigation_list)
    return dref
