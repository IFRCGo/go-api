from typing import List, Any

from rest_framework import serializers
from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedInterventionIndicators,
    RiskSecurity,
)
from api.models import (
    DisasterType,
    Country,
    District,
)

from .common_utils import (
    parse_int,
    parse_string_to_int,
    parse_date,
    parse_float,
    parse_boolean,
    get_table_data,
    get_paragraphs_data,
    parse_disaster_category,
    parse_contact_information
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
        'Multi-purpose Cash': NationalSocietyAction.Title.MULTI_PURPOSE_CASH,
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
    try:
        return DisasterType.objects.filter(name__icontains=disaster_type).first()
    except ValueError:
        return None


def parse_type_of_onset(onset_type):
    if onset_type == 'Slow':
        return Dref.OnsetType.SLOW
    elif onset_type == 'Sudden':
        return Dref.OnsetType.SUDDEN
    elif onset_type == 'Imminent':
        return Dref.OnsetType.IMMINENT
    return None


def extract_assessment_file(doc, created_by):
    tables = get_table_data(doc)
    paragraphs = get_paragraphs_data(doc)

    # Get item form an array
    def get_nth(items: List[Any], index=0):
        if items and len(items) > index:
            return items[index]
        return None

    def get_table_cells(table_idx):
        table = tables[table_idx]

        def f(r, c, i=0, as_list=False):
            if as_list:
                return table[r][c]
            return get_nth(table[r][c], i)
        return f

    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    data['title'] = paragraphs[1][0] if paragraphs[1] else None
    if data['title'] is None:
        raise serializers.ValidationError('Title should be present')

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

    district = cells(6, 2)
    district_list = []
    if district:
        new_district = district.split(',')
        for d in new_district:
            try:
                district = District.objects.filter(
                    country__name__icontains=cells(6, 0, 1),
                    name__icontains=d
                ).first()
            except District.DoesNotExist:
                pass
            if district is None:
                continue
            district_list.append(district)
    try:
        if paragraphs[6][0] == 'What happened, where and when?':
            description = paragraphs[7] or []
            data['event_description'] = ''.join(description) if description else None
    except IndexError:
        pass

    # National Society Actions
    cells = get_table_cells(1)
    # National Society
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
        NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
    ]
    national_society_actions = []
    for i, title in enumerate(national_society_titles):
        description = cells(i, 1)
        if description :
            national_society_actions.append({
                'title': title,
                'description': description
            })

    # Create National Society objects db level
    national_societies = []
    for national_data in national_society_actions:
        if national_data['description']:
            national = NationalSocietyAction.objects.create(**national_data)
            national_societies.append(national)

    ## Movement Parameters
    cells = get_table_cells(2)

    ifrc_desc = cells(0, 1, as_list=True)
    data['ifrc'] = ''.join(ifrc_desc) if ifrc_desc else None

    partner_national_society_desc = cells(1, 1, as_list=True)
    data['partner_national_society'] = ''.join(partner_national_society_desc) if partner_national_society_desc else None

    icrc_desc = cells(2, 1, as_list=True)
    data['icrc'] = ''.join(icrc_desc) if icrc_desc else None

    # Other actors
    cells = get_table_cells(3)
    data['government_requested_assistance'] = parse_boolean(cells(0, 1))

    national_authorities = cells(1, 2, as_list=True)
    data['national_authorities'] = ''.join(national_authorities) if national_authorities else None

    un_and_other_actors = cells(2, 2, as_list=True)
    data['un_or_other_actor'] = ''.join(un_and_other_actors) if un_and_other_actors else None

    coordination_mechanism = cells(4, 0, as_list=True)
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism) if coordination_mechanism else None

    # Operational Strategy
    try:
        if paragraphs[18][0] == 'Overall objective of the operation':
            operation_description = paragraphs[19] or []
            data['operation_objective'] = ''.join(operation_description) if operation_description else None
    except IndexError:
        pass

    # targeting strategy
    try:
        if paragraphs[20][0] == 'Response strategy rationale':
            response_description = paragraphs[21] or []
            data['response_strategy'] = ''.join(response_description) if response_description else None
    except IndexError:
        pass

    # Targeting Strategy
    try:
        if paragraphs[23][0] == 'Who will be targeted through this operation?':
            people_assisted_description = paragraphs[24] or []
            data['people_assisted'] = ''.join(people_assisted_description) if people_assisted_description else None
    except IndexError:
        pass

    try:
        if paragraphs[26][0] == 'Explain the selection criteria for the targeted population':
            selection_criteria_description = paragraphs[27] or []
            data['selection_criteria'] = ''.join(selection_criteria_description) if selection_criteria_description else None
    except IndexError:
        pass

    # Targeting Population
    cells = get_table_cells(4)
    cats = ['women', 'girls', 'men', 'boys', 'total_targeted_population']
    for i, cat in enumerate(cats):
        data[cat] = parse_string_to_int(cells(i, 1))

    data['people_per_local'] = parse_float(cells(1, 2))
    data['people_per_urban'] = parse_float(cells(1, 3))
    data['disability_people_per'] = parse_float(cells(3, 2))

    # Risk And Security Considerations
    cells = get_table_cells(5)

    mitigation_actions = []
    for i in range(2, 5):
        risk = cells(i, 0)
        mitigation = cells(i, 1)
        mitigation_actions.append({
            'risk': risk,
            'mitigation': mitigation
        })

    mitigation_list = []
    for action in mitigation_actions:
        if action['risk'] or action['mitigation']:
            risk_security = RiskSecurity.objects.create(**action)
            mitigation_list.append(risk_security)
    data['risk_security_concern'] = cells(6, 0)

    # PlannedIntervention Table
    planned_intervention = []
    for i in range(6, 19):
        cells = get_table_cells(i)
        title = cells(0, 1)
        budget = cells(0, 3, 1)
        targeted_population = cells(1, 3)

        indicators = []
        for j in range(3, 6):
            indicators.append({
                'title': cells(j, 0),
                'target': parse_int(cells(j, 2)),
            })

        indicators_object_list = []
        for indicator in indicators:
            if indicator['title']:
                planned_object = PlannedInterventionIndicators.objects.create(**indicator)
                indicators_object_list.append(planned_object)

        priority_description = cells(6, 1)
        planned_data = {
            'title': parse_planned_intervention_title(title),
            'budget': parse_int(budget),
            'person_targeted': parse_int(targeted_population),
            'description': priority_description
        }
        if planned_data['budget'] or planned_data['person_targeted'] or planned_data['description']:
            planned = PlannedIntervention.objects.create(**planned_data)
            planned.indicators.add(*indicators_object_list)
            planned_intervention.append(planned)

    # About Support Service
    try:
        if paragraphs[50][0] == 'How many volunteers and staff involved in the response? Briefly describe their role.':
            human_resource_description = paragraphs[51] or []
            data['human_resource'] = ''.join(human_resource_description) if human_resource_description else None
    except IndexError:
        pass

    try:
        if paragraphs[52][0] == 'Will surge personnel be deployed? Please provide the role profile needed.':
            surge_personnel_deployed_description = paragraphs[53] or []
            data['surge_personnel_deployed'] = ''.join(surge_personnel_deployed_description) if surge_personnel_deployed_description else None
    except IndexError:
        pass

    try:
        national_society_contact = parse_contact_information(paragraphs[60] or [])
        data['national_society_contact_title'] = get_nth(national_society_contact, 2)
        data['national_society_contact_email'] = get_nth(national_society_contact, 4)
        data['national_society_contact_phone_number'] = get_nth(national_society_contact, 6)
        data['national_society_contact_name'] = get_nth(national_society_contact, 0)
    except IndexError:
        pass

    try:
        ifrc_appeal_manager = parse_contact_information(paragraphs[61] or [])
        data['ifrc_appeal_manager_title'] = get_nth(ifrc_appeal_manager, 2)
        data['ifrc_appeal_manager_email'] = get_nth(ifrc_appeal_manager, 4)
        data['ifrc_appeal_manager_phone_number'] = get_nth(ifrc_appeal_manager, 6)
        data['ifrc_appeal_manager_name'] = get_nth(ifrc_appeal_manager, 0)
    except IndexError:
        pass

    try:
        ifrc_project_manager = parse_contact_information(paragraphs[62] or [])
        data['ifrc_project_manager_title'] = get_nth(ifrc_project_manager, 2)
        data['ifrc_project_manager_email'] = get_nth(ifrc_project_manager, 4)
        data['ifrc_project_manager_phone_number'] = get_nth(ifrc_project_manager, 6)
        data['ifrc_project_manager_name'] = get_nth(ifrc_project_manager, 0)
    except IndexError:
        pass

    try:
        ifrc_emergency = parse_contact_information(paragraphs[63] or [])
        data['ifrc_emergency_title'] = get_nth(ifrc_emergency, 2)
        data['ifrc_emergency_email'] = get_nth(ifrc_emergency, 4)
        data['ifrc_emergency_phone_number'] = get_nth(ifrc_emergency, 6)
        data['ifrc_emergency_name'] = get_nth(ifrc_emergency, 0)
    except IndexError:
        # FIXME: raise validation error
        pass

    try:
        media = parse_contact_information(paragraphs[64] or [])
        data['media_contact_title'] = get_nth(media, 2)
        data['media_contact_email'] = get_nth(media, 4)
        data['media_contact_phone_number'] = get_nth(media, 6)
        data['media_contact_name'] = get_nth(media, 0)
    except IndexError:
        # FIXME: raise validation error
        pass

    data['is_published'] = False
    data['national_society'] = country
    data['created_by'] = created_by
    data['is_assessment_report'] = True
    dref = Dref.objects.create(**data)
    dref.planned_interventions.add(*planned_intervention)
    dref.national_society_actions.add(*national_societies)
    print(district_list)
    dref.risk_security.add(*mitigation_list)
    if len(district_list) > 0 and None not in district_list:
        dref.district.add(*district_list)
    return dref
